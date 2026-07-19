"""
AI Commerce OS

Module:
    Base Policy Framework

Responsibility:
    กำหนด Lifecycle และเครื่องมือพื้นฐานสำหรับ Policy Plugin

Design Patterns:
    Abstract Base Class
    Template Method
"""

from __future__ import annotations

import re
from abc import ABC
from time import perf_counter
from typing import Any

from app.policies.models import (
    PatternType,
    PolicyAction,
    PolicyRule,
    PolicyTraceEntry,
    PolicyViolation,
)
from app.policies.runtime_models import (
    PolicyContext,
    PolicyDecision,
)


class BasePolicy(ABC):
    """
    Base class สำหรับ Policy Plugin ทุกประเภท.

    BasePolicy ไม่รู้จัก Shopee, Lazada, LINE หรือแพลตฟอร์มใด
    โดยตรง แต่ทำหน้าที่จัดการ Lifecycle การตรวจ Rule ทั้งหมด
    และคืนผลลัพธ์เป็น PolicyDecision
    """

    def __init__(
        self,
        *,
        name: str,
        version: str = "1.0",
        description: str = "",
        rules: tuple[PolicyRule, ...] = (),
        enabled: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """สร้าง Policy Plugin."""

        cleaned_name = name.strip()
        cleaned_version = version.strip()

        if not cleaned_name:
            raise ValueError(
                "BasePolicy.name ต้องไม่ว่าง"
            )

        if not cleaned_version:
            raise ValueError(
                "BasePolicy.version ต้องไม่ว่าง"
            )

        self._name = cleaned_name
        self._version = cleaned_version
        self._description = description.strip()
        self._rules = tuple(rules)
        self._enabled = bool(enabled)
        self._metadata = dict(
            metadata or {}
        )

    @property
    def name(self) -> str:
        """คืนชื่อ Policy."""

        return self._name

    @property
    def version(self) -> str:
        """คืน Version ของ Policy."""

        return self._version

    @property
    def description(self) -> str:
        """คืนคำอธิบาย Policy."""

        return self._description

    @property
    def enabled(self) -> bool:
        """คืนสถานะเปิดใช้งาน Policy."""

        return self._enabled

    @property
    def metadata(self) -> dict[str, Any]:
        """คืนสำเนา Metadata."""

        return dict(
            self._metadata
        )

    @property
    def rules(self) -> tuple[PolicyRule, ...]:
        """คืน Rule ทั้งหมด."""

        return self._rules

    @property
    def enabled_rules(self) -> tuple[PolicyRule, ...]:
        """คืน Rule ที่เปิดใช้งาน เรียงตาม Priority."""

        active_rules = [
            rule
            for rule in self._rules
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

    def can_execute(
        self,
        context: PolicyContext,
    ) -> bool:
        """
        ตรวจว่า Policy สามารถทำงานกับ Context นี้หรือไม่.

        Policy ลูกสามารถ Override เพื่อเพิ่มเงื่อนไข เช่น
        ตรวจเฉพาะแพลตฟอร์มที่กำหนด
        """

        return (
            self.enabled
            and context.has_reply
        )

    def before_execute(
        self,
        context: PolicyContext,
    ) -> None:
        """
        Hook ก่อนเริ่มตรวจ Policy.

        ค่าเริ่มต้นไม่ทำอะไร Policy ลูกสามารถ Override ได้
        """

        del context

    def after_execute(
        self,
        context: PolicyContext,
        decision: PolicyDecision,
    ) -> None:
        """
        Hook หลังตรวจ Policy เสร็จ.

        ค่าเริ่มต้นไม่ทำอะไร Policy ลูกสามารถ Override ได้
        """

        del context
        del decision
    def execute(
        self,
        context: PolicyContext,
    ) -> PolicyDecision:
        """
        ประมวลผล Policy ตาม Lifecycle มาตรฐาน.

        Flow:
            can_execute
            before_execute
            evaluate
            auto_fix
            after_execute
            timing
            metadata
        """

        started_at = perf_counter()

        decision = PolicyDecision(
            policy_name=self.name,
            original_reply=(
                context.effective_reply
            ),
            sanitized_reply=(
                context.effective_reply
            ),
            metadata={
                "policy_version": (
                    self.version
                ),
                "policy_description": (
                    self.description
                ),
                **self.metadata,
            },
        )

        try:
            if not self.can_execute(
                context
            ):
                decision.add_warning(
                    self._build_skip_reason(
                        context
                    )
                )

                decision.metadata[
                    "executed"
                ] = False

                return decision

            decision.metadata[
                "executed"
            ] = True

            self.before_execute(
                context
            )

            evaluated_decision = (
                self.evaluate(
                    context
                )
            )

            decision = self._merge_decisions(
                base_decision=decision,
                evaluated_decision=(
                    evaluated_decision
                ),
            )

            if decision.has_violations:
                fixed_reply = self.auto_fix(
                    context=context,
                    decision=decision,
                )

                if fixed_reply is not None:
                    decision.set_sanitized_reply(
                        fixed_reply
                    )

                    context.update_sanitized_reply(
                        fixed_reply
                    )

            self.after_execute(
                context=context,
                decision=decision,
            )

            decision.refresh_status()

            return decision

        except Exception as error:
            decision.passed = False
            decision.requires_human_review = True

            decision.add_warning(
                "Policy ประมวลผลไม่สำเร็จ "
                "และต้องให้เจ้าหน้าที่ตรวจสอบ"
            )

            decision.metadata[
                "execution_error"
            ] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            return decision

        finally:
            elapsed_ms = (
                perf_counter()
                - started_at
            ) * 1000

            decision.execution_time_ms = max(
                elapsed_ms,
                0.0,
            )

    def evaluate(
        self,
        context: PolicyContext,
    ) -> PolicyDecision:
        """
        ตรวจ Rule ทั้งหมดกับข้อความปัจจุบัน.

        Policy ลูกสามารถ Override เมื่อต้องการ Logic เฉพาะทาง
        แต่ค่าเริ่มต้นรองรับ Keyword และ Regex แล้ว
        """

        reply = context.effective_reply

        decision = PolicyDecision(
            policy_name=self.name,
            original_reply=reply,
            sanitized_reply=reply,
            metadata={
                "policy_version": (
                    self.version
                ),
            },
        )

        for rule in self.enabled_rules:
            started_at = perf_counter()

            matched_text = (
                self.match_rule(
                    rule=rule,
                    text=reply,
                    context=context,
                )
            )

            elapsed_ms = (
                perf_counter()
                - started_at
            ) * 1000

            if matched_text is None:
                decision.add_trace(
                    self.create_trace(
                        rule=rule,
                        passed=True,
                        message=(
                            "ไม่พบข้อความที่ตรงกับกฎ"
                        ),
                        execution_time_ms=(
                            elapsed_ms
                        ),
                    )
                )

                continue

            violation = (
                self.create_violation(
                    rule=rule,
                    matched_text=(
                        matched_text
                    ),
                    context=context,
                )
            )

            decision.add_violation(
                violation
            )

            decision.add_trace(
                self.create_trace(
                    rule=rule,
                    passed=False,
                    message=(
                        violation.message
                    ),
                    execution_time_ms=(
                        elapsed_ms
                    ),
                )
            )

            if rule.action == PolicyAction.WARN:
                decision.add_warning(
                    violation.message
                )

        decision.refresh_status()

        return decision

    def match_rule(
        self,
        *,
        rule: PolicyRule,
        text: str,
        context: PolicyContext,
    ) -> str | None:
        """
        ตรวจว่า Rule ตรงกับข้อความหรือไม่.

        คืนข้อความที่ตรงรายการแรก หรือ None เมื่อไม่พบ
        """

        del context

        if not text.strip():
            return None

        if rule.pattern_type == PatternType.KEYWORD:
            return self._match_keyword_rule(
                rule=rule,
                text=text,
            )

        if rule.pattern_type == PatternType.REGEX:
            return self._match_regex_rule(
                rule=rule,
                text=text,
            )

        raise ValueError(
            "ไม่รองรับ PatternType: "
            f"{rule.pattern_type}"
        )
    def auto_fix(
        self,
        *,
        context: PolicyContext,
        decision: PolicyDecision,
    ) -> str | None:
        """
        แก้ข้อความอัตโนมัติตาม Violation แบบ AUTO_FIX.

        ใช้ข้อความล่าสุดจาก Context เป็นจุดเริ่มต้น
        """

        sanitized_reply = (
            context.effective_reply
        )

        changed = False

        for violation in decision.violations:
            if not violation.can_auto_fix:
                continue

            if not violation.matched_text:
                continue

            sanitized_reply = (
                sanitized_reply.replace(
                    violation.matched_text,
                    violation.replacement_text,
                )
            )

            changed = True

        if not changed:
            return None

        return sanitized_reply.strip()

    def create_violation(
        self,
        *,
        rule: PolicyRule,
        matched_text: str,
        context: PolicyContext,
    ) -> PolicyViolation:
        """สร้าง PolicyViolation จาก Rule ที่ตรวจพบ."""

        return PolicyViolation(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            severity=rule.severity,
            action=rule.action,
            matched_text=matched_text,
            message=(
                self._build_violation_message(
                    rule=rule,
                    matched_text=(
                        matched_text
                    ),
                )
            ),
            suggestion=rule.suggestion,
            replacement_text=(
                rule.replacement_text
            ),
            metadata={
                "policy_name": self.name,
                "policy_version": (
                    self.version
                ),
                "platform": (
                    context.platform
                ),
                "rule_version": (
                    rule.version
                ),
                "rule_owner": rule.owner,
                "rule_tags": list(
                    rule.tags
                ),
            },
        )

    def create_trace(
        self,
        *,
        rule: PolicyRule,
        passed: bool,
        message: str,
        execution_time_ms: float,
    ) -> PolicyTraceEntry:
        """สร้าง Trace ของการตรวจ Rule."""

        return PolicyTraceEntry(
            rule_id=rule.rule_id,
            passed=passed,
            action=rule.action,
            message=message,
            execution_time_ms=max(
                float(
                    execution_time_ms
                ),
                0.0,
            ),
        )

    def _match_keyword_rule(
        self,
        *,
        rule: PolicyRule,
        text: str,
    ) -> str | None:
        """ตรวจ Keyword แบบไม่สนตัวพิมพ์ใหญ่เล็ก."""

        normalized_text = text.lower()

        for pattern in rule.patterns:
            cleaned_pattern = (
                pattern.strip()
            )

            if not cleaned_pattern:
                continue

            if (
                cleaned_pattern.lower()
                in normalized_text
            ):
                return cleaned_pattern

        return None

    def _match_regex_rule(
        self,
        *,
        rule: PolicyRule,
        text: str,
    ) -> str | None:
        """ตรวจ Regular Expression ตามลำดับ Pattern."""

        for pattern in rule.patterns:
            cleaned_pattern = (
                pattern.strip()
            )

            if not cleaned_pattern:
                continue

            try:
                match = re.search(
                    cleaned_pattern,
                    text,
                    flags=re.IGNORECASE,
                )

            except re.error as error:
                raise ValueError(
                    "Regex ไม่ถูกต้องใน Rule "
                    f"{rule.rule_id}: {error}"
                ) from error

            if match is not None:
                return match.group(0)

        return None

    def _merge_decisions(
        self,
        *,
        base_decision: PolicyDecision,
        evaluated_decision: PolicyDecision,
    ) -> PolicyDecision:
        """รวมผล Evaluate เข้ากับ Decision หลัก."""

        for violation in (
            evaluated_decision.violations
        ):
            base_decision.add_violation(
                violation
            )

        for warning in (
            evaluated_decision.warnings
        ):
            base_decision.add_warning(
                warning
            )

        for trace_entry in (
            evaluated_decision.trace
        ):
            base_decision.add_trace(
                trace_entry
            )

        if (
            evaluated_decision
            .sanitized_reply
        ):
            base_decision.set_sanitized_reply(
                evaluated_decision
                .sanitized_reply
            )

        if (
            evaluated_decision
            .requires_human_review
        ):
            base_decision.requires_human_review = (
                True
            )

        base_decision.metadata.update(
            evaluated_decision.metadata
        )

        base_decision.refresh_status()

        return base_decision

    def _build_violation_message(
        self,
        *,
        rule: PolicyRule,
        matched_text: str,
    ) -> str:
        """สร้างข้อความอธิบาย Violation."""

        return (
            f"พบการละเมิดกฎ {rule.rule_id} "
            f"({rule.name}) จากข้อความ "
            f"{matched_text!r}"
        )

    def _build_skip_reason(
        self,
        context: PolicyContext,
    ) -> str:
        """สร้างเหตุผลเมื่อ Policy ไม่ทำงาน."""

        if not self.enabled:
            return (
                f"Policy {self.name} "
                "ถูกปิดใช้งาน"
            )

        if not context.has_reply:
            return (
                f"Policy {self.name} "
                "ไม่มีข้อความสำหรับตรวจสอบ"
            )

        return (
            f"Policy {self.name} "
            "ไม่ตรงเงื่อนไขการทำงาน"
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลงข้อมูล Policy Plugin เป็น Dictionary."""

        return {
            "name": self.name,
            "version": self.version,
            "description": (
                self.description
            ),
            "enabled": self.enabled,
            "rule_count": len(
                self.rules
            ),
            "enabled_rule_count": len(
                self.enabled_rules
            ),
            "rules": [
                rule.to_dict()
                for rule in self.rules
            ],
            "metadata": self.metadata,
        }