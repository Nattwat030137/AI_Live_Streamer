"""Data models กลางสำหรับ AI Governance และ Platform Policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleCategory(str, Enum):
    """หมวดหมู่ของกฎ Governance."""

    BUSINESS = "business"
    PLATFORM = "platform"
    SAFETY = "safety"
    PRIVACY = "privacy"
    LEGAL = "legal"
    MARKETING = "marketing"
    COMPLIANCE = "compliance"
    QUALITY = "quality"


class Severity(str, Enum):
    """ระดับความรุนแรงของ Policy Violation."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyAction(str, Enum):
    """การกระทำเมื่อกฎตรงกับข้อความ."""

    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    AUTO_FIX = "auto_fix"
    HUMAN_HANDOFF = "human_handoff"


class PatternType(str, Enum):
    """ประเภทการตรวจข้อความของ Policy Rule."""

    KEYWORD = "keyword"
    REGEX = "regex"


SEVERITY_RISK_SCORES: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 10,
    Severity.MEDIUM: 30,
    Severity.HIGH: 60,
    Severity.CRITICAL: 100,
}


@dataclass(frozen=True, slots=True)
class PolicyExample:
    """ตัวอย่างข้อความประกอบ Policy Rule."""

    text: str
    description: str = ""

    def __post_init__(self) -> None:
        """ตรวจว่าตัวอย่างมีข้อความ."""

        if not self.text.strip():
            raise ValueError(
                "PolicyExample.text ต้องไม่ว่าง"
            )


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """กฎหนึ่งรายการสำหรับ Governance Engine."""

    rule_id: str
    name: str
    category: RuleCategory
    severity: Severity
    description: str
    patterns: tuple[str, ...] = ()
    pattern_type: PatternType = PatternType.KEYWORD
    action: PolicyAction = PolicyAction.WARN
    replacement_text: str = ""
    suggestion: str = ""
    enabled: bool = True
    priority: int = 50
    version: str = "1.0"
    tags: tuple[str, ...] = ()
    owner: str = "engineering"
    good_examples: tuple[PolicyExample, ...] = ()
    bad_examples: tuple[PolicyExample, ...] = ()
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """ตรวจความถูกต้องพื้นฐานของ Rule."""

        if not self.rule_id.strip():
            raise ValueError(
                "PolicyRule.rule_id ต้องไม่ว่าง"
            )

        if not self.name.strip():
            raise ValueError(
                "PolicyRule.name ต้องไม่ว่าง"
            )

        if not self.description.strip():
            raise ValueError(
                "PolicyRule.description ต้องไม่ว่าง"
            )

        if self.priority < 0:
            raise ValueError(
                "PolicyRule.priority ต้องไม่น้อยกว่า 0"
            )

        if (
            self.action == PolicyAction.AUTO_FIX
            and not self.replacement_text.strip()
        ):
            raise ValueError(
                "AUTO_FIX ต้องมี replacement_text"
            )

    @property
    def risk_score(self) -> int:
        """คืนคะแนนความเสี่ยงพื้นฐานจาก Severity."""

        return SEVERITY_RISK_SCORES[
            self.severity
        ]

    @property
    def is_blocking(self) -> bool:
        """คืน True เมื่อกฎสามารถบล็อกข้อความ."""

        return self.action in {
            PolicyAction.BLOCK,
            PolicyAction.HUMAN_HANDOFF,
        }

    @property
    def requires_human_review(self) -> bool:
        """คืน True เมื่อกฎกำหนดให้มนุษย์ตรวจสอบ."""

        return (
            self.action
            == PolicyAction.HUMAN_HANDOFF
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Rule เป็น Dictionary."""

        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "patterns": list(
                self.patterns
            ),
            "pattern_type": (
                self.pattern_type.value
            ),
            "action": self.action.value,
            "replacement_text": (
                self.replacement_text
            ),
            "suggestion": self.suggestion,
            "enabled": self.enabled,
            "priority": self.priority,
            "version": self.version,
            "tags": list(
                self.tags
            ),
            "owner": self.owner,
            "good_examples": [
                {
                    "text": example.text,
                    "description": (
                        example.description
                    ),
                }
                for example
                in self.good_examples
            ],
            "bad_examples": [
                {
                    "text": example.text,
                    "description": (
                        example.description
                    ),
                }
                for example
                in self.bad_examples
            ],
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    """รายละเอียดการละเมิด Policy หนึ่งรายการ."""

    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: Severity
    action: PolicyAction
    matched_text: str = ""
    message: str = ""
    suggestion: str = ""
    replacement_text: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def risk_score(self) -> int:
        """คืนคะแนนความเสี่ยงของ Violation."""

        return SEVERITY_RISK_SCORES[
            self.severity
        ]

    @property
    def blocks_message(self) -> bool:
        """คืน True เมื่อ Violation ต้องบล็อกข้อความ."""

        return self.action in {
            PolicyAction.BLOCK,
            PolicyAction.HUMAN_HANDOFF,
        }

    @property
    def can_auto_fix(self) -> bool:
        """คืน True เมื่อ Violation แก้อัตโนมัติได้."""

        return (
            self.action == PolicyAction.AUTO_FIX
            and bool(
                self.replacement_text.strip()
            )
        )

    @property
    def requires_human_review(self) -> bool:
        """คืน True เมื่อควรส่งให้มนุษย์ตรวจสอบ."""

        return (
            self.action
            == PolicyAction.HUMAN_HANDOFF
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Violation เป็น Dictionary."""

        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "action": self.action.value,
            "matched_text": self.matched_text,
            "message": self.message,
            "suggestion": self.suggestion,
            "replacement_text": (
                self.replacement_text
            ),
            "risk_score": self.risk_score,
            "blocks_message": (
                self.blocks_message
            ),
            "can_auto_fix": (
                self.can_auto_fix
            ),
            "requires_human_review": (
                self.requires_human_review
            ),
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(frozen=True, slots=True)
class PolicyTraceEntry:
    """ประวัติการตรวจ Policy Rule หนึ่งรายการ."""

    rule_id: str
    passed: bool
    action: PolicyAction
    message: str = ""
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """แปลง Trace Entry เป็น Dictionary."""

        return {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "action": self.action.value,
            "message": self.message,
            "execution_time_ms": (
                self.execution_time_ms
            ),
        }


@dataclass(slots=True)
class PolicyResult:
    """ผลรวมจากการตรวจ Governance Policy."""

    original_reply: str
    sanitized_reply: str
    platform: str = "generic"
    policy_version: str = "1.0"
    allowed: bool = True
    compliance_score: int = 100
    risk_score: int = 0
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

    @property
    def has_violations(self) -> bool:
        """คืน True เมื่อพบ Violation."""

        return bool(
            self.violations
        )

    @property
    def has_critical_violation(self) -> bool:
        """คืน True เมื่อพบระดับ Critical."""

        return any(
            violation.severity
            == Severity.CRITICAL
            for violation in self.violations
        )

    @property
    def blocked_rule_ids(self) -> list[str]:
        """คืน Rule ID ที่บล็อกข้อความ."""

        return [
            violation.rule_id
            for violation in self.violations
            if violation.blocks_message
        ]

    @property
    def violation_categories(
        self,
    ) -> list[RuleCategory]:
        """คืนหมวด Violation โดยไม่ซ้ำ."""

        categories: list[
            RuleCategory
        ] = []

        for violation in self.violations:
            if violation.category in categories:
                continue

            categories.append(
                violation.category
            )

        return categories

    def add_violation(
        self,
        violation: PolicyViolation,
    ) -> None:
        """เพิ่ม Violation และอัปเดตผลรวม."""

        self.violations.append(
            violation
        )

        self.risk_score = min(
            100,
            self.risk_score
            + violation.risk_score,
        )

        self.compliance_score = max(
            0,
            100 - self.risk_score,
        )

        if violation.blocks_message:
            self.allowed = False

        if violation.requires_human_review:
            self.requires_human_review = True

        if (
            violation.severity
            == Severity.CRITICAL
        ):
            self.allowed = False
            self.requires_human_review = True

    def add_warning(
        self,
        warning: str,
    ) -> None:
        """เพิ่ม Warning โดยไม่เก็บข้อความซ้ำ."""

        cleaned_warning = warning.strip()

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
        """เพิ่ม Policy Trace."""

        self.trace.append(
            entry
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Policy Result เป็น Dictionary."""

        return {
            "original_reply": (
                self.original_reply
            ),
            "sanitized_reply": (
                self.sanitized_reply
            ),
            "platform": self.platform,
            "policy_version": (
                self.policy_version
            ),
            "allowed": self.allowed,
            "compliance_score": (
                self.compliance_score
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
                for entry in self.trace
            ],
            "requires_human_review": (
                self.requires_human_review
            ),
            "execution_time_ms": (
                self.execution_time_ms
            ),
            "blocked_rule_ids": (
                self.blocked_rule_ids
            ),
            "violation_categories": [
                category.value
                for category
                in self.violation_categories
            ],
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(frozen=True, slots=True)
class PlatformProfile:
    """โปรไฟล์ Policy สำหรับแพลตฟอร์มหนึ่งช่องทาง."""

    platform_name: str
    version: str
    description: str = ""
    rules: tuple[PolicyRule, ...] = ()
    enabled: bool = True
    max_reply_length: int | None = None
    default_tone: str = (
        "สุภาพและเป็นธรรมชาติ"
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """ตรวจความถูกต้องพื้นฐานของ Profile."""

        if not self.platform_name.strip():
            raise ValueError(
                "platform_name ต้องไม่ว่าง"
            )

        if not self.version.strip():
            raise ValueError(
                "PlatformProfile.version ต้องไม่ว่าง"
            )

        if (
            self.max_reply_length is not None
            and self.max_reply_length <= 0
        ):
            raise ValueError(
                "max_reply_length ต้องมากกว่า 0"
            )

    @property
    def enabled_rules(self) -> tuple[PolicyRule, ...]:
        """คืนกฎที่เปิดใช้งาน เรียงตาม Priority."""

        active_rules = [
            rule
            for rule in self.rules
            if rule.enabled
        ]

        return tuple(
            sorted(
                active_rules,
                key=lambda rule: (
                    rule.priority
                ),
                reverse=True,
            )
        )

    def get_rule(
        self,
        rule_id: str,
    ) -> PolicyRule | None:
        """ค้น Rule จาก Rule ID."""

        normalized_rule_id = (
            rule_id.strip().lower()
        )

        for rule in self.rules:
            if (
                rule.rule_id.lower()
                == normalized_rule_id
            ):
                return rule

        return None

    def to_dict(self) -> dict[str, Any]:
        """แปลง Profile เป็น Dictionary."""

        return {
            "platform_name": (
                self.platform_name
            ),
            "version": self.version,
            "description": (
                self.description
            ),
            "rules": [
                rule.to_dict()
                for rule in self.rules
            ],
            "enabled": self.enabled,
            "max_reply_length": (
                self.max_reply_length
            ),
            "default_tone": (
                self.default_tone
            ),
            "metadata": dict(
                self.metadata
            ),
        }