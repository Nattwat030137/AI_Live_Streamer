"""Runtime models สำหรับการประมวลผล AI Governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.policies.models import (
    PolicyTraceEntry,
    PolicyViolation,
)


@dataclass(slots=True)
class PolicyContext:
    """
    ข้อมูลกลางที่ส่งให้ Policy Plugin ตรวจสอบ.

    Model นี้ไม่ผูกกับ Shopee, Lazada หรือแพลตฟอร์มใด
    เพื่อให้ Governance Core ใช้ร่วมกันได้ทุกช่องทาง
    """

    original_reply: str
    platform: str = "generic"

    customer_message: str = ""
    sanitized_reply: str = ""

    customer_intent: str = ""
    emotion: str = ""
    persona: str = ""
    pipeline_stage: str = ""
    primary_action: str = ""

    intent_score: int = 0
    emotion_score: int = 0
    persona_confidence: int = 0
    sales_confidence: int = 0
    knowledge_confidence: int = 0

    recommendation_keywords: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """ปรับข้อมูลพื้นฐานและตรวจค่าคะแนน."""

        self.original_reply = (
            self.original_reply.strip()
        )

        self.platform = (
            self.platform.strip().lower()
            or "generic"
        )

        if not self.sanitized_reply:
            self.sanitized_reply = (
                self.original_reply
            )

        self.sanitized_reply = (
            self.sanitized_reply.strip()
        )

        self.intent_score = clamp_score(
            self.intent_score
        )

        self.emotion_score = clamp_score(
            self.emotion_score
        )

        self.persona_confidence = clamp_score(
            self.persona_confidence
        )

        self.sales_confidence = clamp_score(
            self.sales_confidence
        )

        self.knowledge_confidence = clamp_score(
            self.knowledge_confidence
        )

    @property
    def effective_reply(self) -> str:
        """คืนข้อความล่าสุดที่ Policy ควรตรวจ."""

        return (
            self.sanitized_reply
            or self.original_reply
        )

    @property
    def has_reply(self) -> bool:
        """คืน True เมื่อมีข้อความให้ตรวจ."""

        return bool(
            self.effective_reply.strip()
        )

    @property
    def requires_low_confidence_review(
        self,
    ) -> bool:
        """
        คืน True เมื่อข้อมูลมีความมั่นใจต่ำ.

        ใช้เป็นสัญญาณให้ Policy หรือ Governance Engine
        พิจารณาส่งต่อแอดมิน
        """

        confidence_values = [
            score
            for score in (
                self.sales_confidence,
                self.knowledge_confidence,
            )
            if score > 0
        ]

        if not confidence_values:
            return False

        return min(
            confidence_values
        ) < 40

    def update_sanitized_reply(
        self,
        reply: str,
    ) -> None:
        """อัปเดตข้อความหลัง Policy แก้ไข."""

        self.sanitized_reply = (
            reply.strip()
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Policy Context เป็น Dictionary."""

        return {
            "original_reply": (
                self.original_reply
            ),
            "sanitized_reply": (
                self.sanitized_reply
            ),
            "effective_reply": (
                self.effective_reply
            ),
            "platform": self.platform,
            "customer_message": (
                self.customer_message
            ),
            "customer_intent": (
                self.customer_intent
            ),
            "emotion": self.emotion,
            "persona": self.persona,
            "pipeline_stage": (
                self.pipeline_stage
            ),
            "primary_action": (
                self.primary_action
            ),
            "intent_score": (
                self.intent_score
            ),
            "emotion_score": (
                self.emotion_score
            ),
            "persona_confidence": (
                self.persona_confidence
            ),
            "sales_confidence": (
                self.sales_confidence
            ),
            "knowledge_confidence": (
                self.knowledge_confidence
            ),
            "recommendation_keywords": list(
                self.recommendation_keywords
            ),
            "requires_low_confidence_review": (
                self.requires_low_confidence_review
            ),
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(slots=True)
class PolicyDecision:
    """
    ผลการตรวจจาก Policy Plugin หนึ่งตัว.

    Plugin คืน Decision กลับมาแทนการแก้ PolicyResult
    โดยตรง ทำให้แต่ละ Plugin แยกจากกันและ Test ง่าย
    """

    policy_name: str
    passed: bool = True

    original_reply: str = ""
    sanitized_reply: str = ""

    violations: list[PolicyViolation] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    trace: list[PolicyTraceEntry] = field(
        default_factory=list
    )

    requires_human_review: bool = False
    execution_time_ms: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """ตรวจและปรับข้อมูลเริ่มต้น."""

        self.policy_name = (
            self.policy_name.strip()
        )

        if not self.policy_name:
            raise ValueError(
                "PolicyDecision.policy_name "
                "ต้องไม่ว่าง"
            )

        self.execution_time_ms = max(
            float(
                self.execution_time_ms
            ),
            0.0,
        )

        self.refresh_status()

    @property
    def has_violations(self) -> bool:
        """คืน True เมื่อพบ Violation."""

        return bool(
            self.violations
        )

    @property
    def has_blocking_violation(
        self,
    ) -> bool:
        """คืน True เมื่อพบกฎที่ต้องบล็อกข้อความ."""

        return any(
            violation.blocks_message
            for violation in self.violations
        )

    @property
    def has_auto_fix(self) -> bool:
        """คืน True เมื่อข้อความถูกแก้โดย Policy."""

        return (
            bool(
                self.sanitized_reply.strip()
            )
            and self.sanitized_reply.strip()
            != self.original_reply.strip()
        )

    @property
    def risk_score(self) -> int:
        """รวมคะแนนความเสี่ยงไม่เกิน 100."""

        return min(
            100,
            sum(
                violation.risk_score
                for violation
                in self.violations
            ),
        )

    def refresh_status(self) -> None:
        """อัปเดตสถานะจาก Violation ปัจจุบัน."""

        if self.has_blocking_violation:
            self.passed = False

        if any(
            violation.requires_human_review
            for violation in self.violations
        ):
            self.requires_human_review = True

    def add_violation(
        self,
        violation: PolicyViolation,
    ) -> None:
        """เพิ่ม Violation และอัปเดตสถานะ."""

        self.violations.append(
            violation
        )

        self.refresh_status()

    def add_warning(
        self,
        warning: str,
    ) -> None:
        """เพิ่ม Warning โดยไม่เก็บข้อความซ้ำ."""

        cleaned_warning = (
            warning.strip()
        )

        if not cleaned_warning:
            return

        if cleaned_warning in self.warnings:
            return

        self.warnings.append(
            cleaned_warning
        )

    def add_trace(
        self,
        entry: PolicyTraceEntry,
    ) -> None:
        """เพิ่ม Trace ของ Policy."""

        self.trace.append(
            entry
        )

    def set_sanitized_reply(
        self,
        reply: str,
    ) -> None:
        """กำหนดข้อความหลัง Auto Fix."""

        self.sanitized_reply = (
            reply.strip()
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Policy Decision เป็น Dictionary."""

        self.refresh_status()

        return {
            "policy_name": (
                self.policy_name
            ),
            "passed": self.passed,
            "original_reply": (
                self.original_reply
            ),
            "sanitized_reply": (
                self.sanitized_reply
            ),
            "has_violations": (
                self.has_violations
            ),
            "has_blocking_violation": (
                self.has_blocking_violation
            ),
            "has_auto_fix": (
                self.has_auto_fix
            ),
            "risk_score": (
                self.risk_score
            ),
            "violations": [
                violation.to_dict()
                for violation
                in self.violations
            ],
            "warnings": list(
                self.warnings
            ),
            "trace": [
                entry.to_dict()
                for entry
                in self.trace
            ],
            "requires_human_review": (
                self.requires_human_review
            ),
            "execution_time_ms": (
                self.execution_time_ms
            ),
            "metadata": dict(
                self.metadata
            ),
        }


def clamp_score(
    score: int,
) -> int:
    """จำกัดคะแนนให้อยู่ระหว่าง 0 ถึง 100."""

    return max(
        0,
        min(
            int(
                score
            ),
            100,
        ),
    )