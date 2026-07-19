"""
AI Commerce OS

Module:
    Governance Engine

Responsibility:
    ประมวลผล Policy Plugins จาก Registry
    รวม PolicyDecision และคืน PolicyResult

Design Patterns:
    Pipeline
    Aggregator
    Dependency Inversion
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.policies.models import (
    PolicyResult,
)
from app.policies.registry import (
    PolicyRegistry,
    get_default_registry,
)
from app.policies.runtime_models import (
    PolicyContext,
    PolicyDecision,
)


class GovernanceEngine:
    """
    Engine กลางสำหรับประมวลผล AI Governance Policies.

    Engine ไม่รู้จักกฎของ Shopee, Lazada, LINE หรือ Business
    โดยตรง แต่รับ Policy Plugins จาก PolicyRegistry และเรียกใช้
    ผ่าน BasePolicy Interface เท่านั้น
    """

    def __init__(
        self,
        registry: PolicyRegistry | None = None,
        *,
        stop_on_block: bool = False,
        include_disabled: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        สร้าง Governance Engine.

        Args:
            registry:
                Registry ที่เก็บ Policy Plugins หากไม่ระบุ
                จะใช้ Default Registry
            stop_on_block:
                หยุด Pipeline ทันทีเมื่อพบ Blocking Violation
            include_disabled:
                รวม Policy ที่ปิดใช้งานไว้ใน Pipeline หรือไม่
            metadata:
                Metadata เพิ่มเติมของ Engine
        """

        self._registry = (
            registry
            if registry is not None
            else get_default_registry()
        )

        self._stop_on_block = bool(
            stop_on_block
        )

        self._include_disabled = bool(
            include_disabled
        )

        self._metadata = dict(
            metadata or {}
        )

    @property
    def registry(self) -> PolicyRegistry:
        """คืน Policy Registry ที่ Engine ใช้งาน."""

        return self._registry

    @property
    def stop_on_block(self) -> bool:
        """คืนสถานะการหยุด Pipeline เมื่อพบ Block."""

        return self._stop_on_block

    @property
    def include_disabled(self) -> bool:
        """คืนสถานะการรวม Disabled Policy."""

        return self._include_disabled

    @property
    def metadata(self) -> dict[str, Any]:
        """คืนสำเนา Metadata ของ Engine."""

        return dict(
            self._metadata
        )

    def evaluate(
        self,
        context: PolicyContext,
    ) -> PolicyResult:
        """
        ประมวลผล Policy Pipeline และคืนผลรวม.

        Flow:
            PolicyContext
            → Registry execution order
            → Policy.execute()
            → PolicyDecision
            → Aggregate
            → PolicyResult
        """

        if not isinstance(
            context,
            PolicyContext,
        ):
            raise TypeError(
                "context ต้องเป็น PolicyContext"
            )

        started_at = perf_counter()

        result = self._create_result(
            context
        )

        decisions: list[
            PolicyDecision
        ] = []

        policies = (
            self.registry.execution_order(
                platform=context.platform,
                enabled_only=(
                    not self.include_disabled
                ),
            )
        )

        result.metadata[
            "registered_policy_count"
        ] = self.registry.count

        result.metadata[
            "selected_policy_count"
        ] = len(
            policies
        )

        try:
            for policy in policies:
                decision = policy.execute(
                    context
                )

                decisions.append(
                    decision
                )

                self._aggregate_decision(
                    result=result,
                    decision=decision,
                    context=context,
                )

                if (
                    self.stop_on_block
                    and decision
                    .has_blocking_violation
                ):
                    result.metadata[
                        "pipeline_stopped"
                    ] = True

                    result.metadata[
                        "stopped_by_policy"
                    ] = policy.name

                    break

            else:
                result.metadata[
                    "pipeline_stopped"
                ] = False

            self._finalize_result(
                result=result,
                context=context,
                decisions=decisions,
            )

            return result

        except Exception as error:
            result.allowed = False
            result.requires_human_review = True

            result.add_warning(
                "Governance Engine "
                "ประมวลผลไม่สำเร็จ "
                "และต้องให้เจ้าหน้าที่ตรวจสอบ"
            )

            result.metadata[
                "engine_error"
            ] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            return result

        finally:
            elapsed_ms = (
                perf_counter()
                - started_at
            ) * 1000

            result.execution_time_ms = max(
                elapsed_ms,
                0.0,
            )

    def evaluate_reply(
        self,
        reply: str,
        *,
        platform: str = "generic",
        customer_message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> PolicyResult:
        """
        Convenience Method สำหรับตรวจข้อความโดยตรง.

        เหมาะกับการเรียกใช้งานจาก AI Engine หรือการทดสอบ
        ที่ยังไม่มี PolicyContext เต็มรูปแบบ
        """

        context = PolicyContext(
            original_reply=reply,
            platform=platform,
            customer_message=(
                customer_message
            ),
            metadata=dict(
                metadata or {}
            ),
        )

        return self.evaluate(
            context
        )

    def _create_result(
        self,
        context: PolicyContext,
    ) -> PolicyResult:
        """สร้าง PolicyResult เริ่มต้นจาก Context."""

        return PolicyResult(
            original_reply=(
                context.original_reply
            ),
            sanitized_reply=(
                context.effective_reply
            ),
            platform=context.platform,
            policy_version="1.0",
            metadata={
                "engine": (
                    "governance_engine"
                ),
                "stop_on_block": (
                    self.stop_on_block
                ),
                "include_disabled": (
                    self.include_disabled
                ),
                "context": (
                    context.to_dict()
                ),
                **self.metadata,
            },
        )

    def _aggregate_decision(
        self,
        *,
        result: PolicyResult,
        decision: PolicyDecision,
        context: PolicyContext,
    ) -> None:
        """รวม PolicyDecision หนึ่งรายการเข้า PolicyResult."""

        for violation in decision.violations:
            result.add_violation(
                violation
            )

        for warning in decision.warnings:
            result.add_warning(
                warning
            )

        for trace_entry in decision.trace:
            result.add_trace(
                trace_entry
            )

        if decision.requires_human_review:
            result.requires_human_review = (
                True
            )

        if decision.sanitized_reply.strip():
            result.sanitized_reply = (
                decision
                .sanitized_reply
                .strip()
            )

        if decision.has_auto_fix:
            context.update_sanitized_reply(
                decision.sanitized_reply
            )

            result.sanitized_reply = (
                context.effective_reply
            )

        policy_decisions = (
            result.metadata.setdefault(
                "policy_decisions",
                [],
            )
        )

        policy_decisions.append(
            self._build_decision_summary(
                decision
            )
        )

    def _finalize_result(
        self,
        *,
        result: PolicyResult,
        context: PolicyContext,
        decisions: list[PolicyDecision],
    ) -> None:
        """อัปเดตผลรวมหลัง Policy Pipeline ทำงานครบ."""

        result.sanitized_reply = (
            context.effective_reply
        )

        if result.has_critical_violation:
            result.allowed = False
            result.requires_human_review = (
                True
            )

        if any(
            decision
            .has_blocking_violation
            for decision in decisions
        ):
            result.allowed = False

        if any(
            not decision.passed
            and not decision
            .has_blocking_violation
            for decision in decisions
        ):
            result.requires_human_review = (
                True
            )

        executed_decisions = [
            decision
            for decision in decisions
            if decision.metadata.get(
                "executed",
                True,
            )
        ]

        auto_fixed_decisions = [
            decision
            for decision in decisions
            if decision.has_auto_fix
        ]

        result.metadata[
            "decision_count"
        ] = len(
            decisions
        )

        result.metadata[
            "executed_policy_count"
        ] = len(
            executed_decisions
        )

        result.metadata[
            "auto_fix_count"
        ] = len(
            auto_fixed_decisions
        )

        result.metadata[
            "violation_count"
        ] = len(
            result.violations
        )

        result.metadata[
            "warning_count"
        ] = len(
            result.warnings
        )

        result.metadata[
            "trace_count"
        ] = len(
            result.trace
        )

        result.metadata[
            "final_reply_changed"
        ] = (
            result.sanitized_reply.strip()
            != result.original_reply.strip()
        )

    @staticmethod
    def _build_decision_summary(
        decision: PolicyDecision,
    ) -> dict[str, Any]:
        """สร้างข้อมูลสรุปของ PolicyDecision."""

        return {
            "policy_name": (
                decision.policy_name
            ),
            "passed": decision.passed,
            "risk_score": (
                decision.risk_score
            ),
            "violation_count": len(
                decision.violations
            ),
            "warning_count": len(
                decision.warnings
            ),
            "trace_count": len(
                decision.trace
            ),
            "has_auto_fix": (
                decision.has_auto_fix
            ),
            "has_blocking_violation": (
                decision
                .has_blocking_violation
            ),
            "requires_human_review": (
                decision
                .requires_human_review
            ),
            "execution_time_ms": (
                decision.execution_time_ms
            ),
            "metadata": dict(
                decision.metadata
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """แปลงข้อมูล Governance Engine เป็น Dictionary."""

        return {
            "stop_on_block": (
                self.stop_on_block
            ),
            "include_disabled": (
                self.include_disabled
            ),
            "registered_policy_count": (
                self.registry.count
            ),
            "registry": (
                self.registry.to_dict()
            ),
            "metadata": self.metadata,
        }