"""ทดสอบ BasePolicy ของ AI Governance Framework."""

from __future__ import annotations

from app.policies.base import BasePolicy
from app.policies.models import (
    PatternType,
    PolicyAction,
    PolicyRule,
    RuleCategory,
    Severity,
)
from app.policies.runtime_models import (
    PolicyContext,
    PolicyDecision,
)


class TrackingPolicy(BasePolicy):
    """Policy สำหรับตรวจ Lifecycle และ Hook."""

    def __init__(
        self,
        *,
        rules: tuple[PolicyRule, ...] = (),
        enabled: bool = True,
    ) -> None:
        super().__init__(
            name="tracking_policy",
            version="1.2",
            description="Policy สำหรับ Unit Test",
            rules=rules,
            enabled=enabled,
            metadata={
                "source": "unit_test",
            },
        )

        self.events: list[str] = []

    def can_execute(
        self,
        context: PolicyContext,
    ) -> bool:
        self.events.append(
            "can_execute"
        )

        return super().can_execute(
            context
        )

    def before_execute(
        self,
        context: PolicyContext,
    ) -> None:
        del context

        self.events.append(
            "before_execute"
        )

    def evaluate(
        self,
        context: PolicyContext,
    ) -> PolicyDecision:
        self.events.append(
            "evaluate"
        )

        return super().evaluate(
            context
        )

    def auto_fix(
        self,
        *,
        context: PolicyContext,
        decision: PolicyDecision,
    ) -> str | None:
        self.events.append(
            "auto_fix"
        )

        return super().auto_fix(
            context=context,
            decision=decision,
        )

    def after_execute(
        self,
        context: PolicyContext,
        decision: PolicyDecision,
    ) -> None:
        del context
        del decision

        self.events.append(
            "after_execute"
        )


class PlatformOnlyPolicy(BasePolicy):
    """Policy ที่ทำงานเฉพาะ Shopee."""

    def can_execute(
        self,
        context: PolicyContext,
    ) -> bool:
        return (
            super().can_execute(
                context
            )
            and context.platform == "shopee"
        )


class BrokenPolicy(BasePolicy):
    """Policy สำหรับทดสอบ Error Handling."""

    def evaluate(
        self,
        context: PolicyContext,
    ) -> PolicyDecision:
        del context

        raise RuntimeError(
            "ทดสอบข้อผิดพลาด"
        )


def assert_raises_value_error(
    factory,
    expected_text: str,
) -> None:
    """ตรวจว่า Callable ต้องเกิด ValueError."""

    try:
        factory()

    except ValueError as error:
        assert expected_text in str(
            error
        )

    else:
        raise AssertionError(
            "ควรเกิด ValueError"
        )


def create_keyword_rules(
) -> tuple[PolicyRule, ...]:
    """สร้างกฎ Keyword สำหรับทดสอบ."""

    warning_rule = PolicyRule(
        rule_id="BUSINESS-001",
        name="Unknown promotion",
        category=RuleCategory.BUSINESS,
        severity=Severity.MEDIUM,
        description=(
            "ห้ามแจ้งโปรโมชั่น"
            "ที่ไม่มีข้อมูลรองรับ"
        ),
        patterns=(
            "ลดเหลือ",
            "โปรโมชั่นพิเศษ",
        ),
        action=PolicyAction.WARN,
        suggestion=(
            "ให้แอดมินตรวจสอบ"
            "โปรโมชั่นล่าสุด"
        ),
        priority=80,
    )

    block_rule = PolicyRule(
        rule_id="SHOPEE-001",
        name="External payment",
        category=RuleCategory.PLATFORM,
        severity=Severity.HIGH,
        description=(
            "ห้ามชำระเงิน"
            "นอกแพลตฟอร์ม"
        ),
        patterns=(
            "โอนเข้าบัญชี",
        ),
        action=PolicyAction.BLOCK,
        priority=100,
    )

    auto_fix_rule = PolicyRule(
        rule_id="SHOPEE-002",
        name="External contact",
        category=RuleCategory.PLATFORM,
        severity=Severity.HIGH,
        description=(
            "ห้ามชักชวนลูกค้า"
            "ไปติดต่อภายนอก"
        ),
        patterns=(
            "แอดไลน์",
        ),
        action=PolicyAction.AUTO_FIX,
        replacement_text=(
            "สอบถามรายละเอียด"
            "ผ่านช่องทางนี้"
        ),
        priority=90,
    )

    disabled_rule = PolicyRule(
        rule_id="TEST-999",
        name="Disabled rule",
        category=RuleCategory.QUALITY,
        severity=Severity.CRITICAL,
        description=(
            "กฎที่ปิดใช้งาน"
        ),
        patterns=(
            "ข้อความต้องห้าม",
        ),
        action=PolicyAction.BLOCK,
        enabled=False,
        priority=999,
    )

    return (
        warning_rule,
        block_rule,
        auto_fix_rule,
        disabled_rule,
    )


def main() -> None:
    """ตรวจ BasePolicy ทุกพฤติกรรมหลัก."""

    rules = create_keyword_rules()

    # --------------------------------------------------
    # Constructor และ Properties
    # --------------------------------------------------

    policy = TrackingPolicy(
        rules=rules
    )

    assert policy.name == (
        "tracking_policy"
    )

    assert policy.version == "1.2"

    assert policy.description == (
        "Policy สำหรับ Unit Test"
    )

    assert policy.enabled

    assert policy.metadata == {
        "source": "unit_test",
    }

    # metadata ต้องเป็นสำเนา
    copied_metadata = policy.metadata

    copied_metadata[
        "new"
    ] = True

    assert policy.metadata == {
        "source": "unit_test",
    }

    assert policy.rules == rules

    # เรียง Priority และตัด Disabled Rule
    assert [
        rule.rule_id
        for rule in policy.enabled_rules
    ] == [
        "SHOPEE-001",
        "SHOPEE-002",
        "BUSINESS-001",
    ]

    policy_dict = policy.to_dict()

    assert policy_dict[
        "name"
    ] == "tracking_policy"

    assert policy_dict[
        "version"
    ] == "1.2"

    assert policy_dict[
        "rule_count"
    ] == 4

    assert policy_dict[
        "enabled_rule_count"
    ] == 3

    # --------------------------------------------------
    # Constructor Validation
    # --------------------------------------------------

    assert_raises_value_error(
        lambda: BasePolicy(
            name="   "
        ),
        "name",
    )

    assert_raises_value_error(
        lambda: BasePolicy(
            name="test",
            version="   ",
        ),
        "version",
    )

    # --------------------------------------------------
    # ไม่มีข้อความ ต้อง Skip
    # --------------------------------------------------

    empty_context = PolicyContext(
        original_reply="   ",
    )

    empty_decision = policy.execute(
        empty_context
    )

    assert empty_decision.passed

    assert not (
        empty_decision.has_violations
    )

    assert empty_decision.metadata[
        "executed"
    ] is False

    assert empty_decision.warnings

    assert "ไม่มีข้อความ" in (
        empty_decision.warnings[0]
    )

    assert (
        empty_decision.execution_time_ms
        >= 0
    )

    # --------------------------------------------------
    # Disabled Policy
    # --------------------------------------------------

    disabled_policy = TrackingPolicy(
        rules=rules,
        enabled=False,
    )

    disabled_context = PolicyContext(
        original_reply="ทดสอบ",
    )

    disabled_decision = (
        disabled_policy.execute(
            disabled_context
        )
    )

    assert disabled_decision.passed

    assert disabled_decision.metadata[
        "executed"
    ] is False

    assert "ปิดใช้งาน" in (
        disabled_decision.warnings[0]
    )

    # --------------------------------------------------
    # ไม่มี Violation
    # --------------------------------------------------

    safe_context = PolicyContext(
        original_reply=(
            "สามารถสอบถามรายละเอียด"
            "เพิ่มเติมได้ค่ะ"
        ),
        platform="shopee",
    )

    safe_policy = TrackingPolicy(
        rules=rules
    )

    safe_decision = safe_policy.execute(
        safe_context
    )

    assert safe_decision.passed
    assert not safe_decision.has_violations
    assert not safe_decision.has_auto_fix
    assert safe_decision.risk_score == 0

    assert len(
        safe_decision.trace
    ) == 3

    assert all(
        trace.passed
        for trace in safe_decision.trace
    )

    assert safe_policy.events == [
        "can_execute",
        "before_execute",
        "evaluate",
        "after_execute",
    ]

    # ไม่มี Violation จึงไม่เรียก auto_fix
    assert "auto_fix" not in (
        safe_policy.events
    )

    # --------------------------------------------------
    # Warning
    # --------------------------------------------------

    warning_context = PolicyContext(
        original_reply=(
            "วันนี้ลดเหลือ 25 บาทค่ะ"
        ),
        platform="website",
    )

    warning_policy = TrackingPolicy(
        rules=rules
    )

    warning_decision = (
        warning_policy.execute(
            warning_context
        )
    )

    assert warning_decision.passed
    assert warning_decision.has_violations
    assert warning_decision.risk_score == 30

    assert len(
        warning_decision.violations
    ) == 1

    assert warning_decision.violations[
        0
    ].rule_id == "BUSINESS-001"

    assert warning_decision.warnings

    assert warning_decision.trace[
        0
    ].rule_id == "SHOPEE-001"

    assert warning_decision.trace[
        -1
    ].rule_id == "BUSINESS-001"

    # --------------------------------------------------
    # Block
    # --------------------------------------------------

    block_context = PolicyContext(
        original_reply=(
            "โอนเข้าบัญชีได้เลยค่ะ"
        ),
        platform="shopee",
    )

    block_policy = TrackingPolicy(
        rules=rules
    )

    block_decision = block_policy.execute(
        block_context
    )

    assert not block_decision.passed

    assert (
        block_decision
        .has_blocking_violation
    )

    assert block_decision.risk_score == 60

    assert block_decision.violations[
        0
    ].rule_id == "SHOPEE-001"

    assert not block_decision.has_auto_fix

    # --------------------------------------------------
    # Auto Fix
    # --------------------------------------------------

    auto_fix_context = PolicyContext(
        original_reply=(
            "แอดไลน์ร้านได้เลยค่ะ"
        ),
        platform="shopee",
    )

    auto_fix_policy = TrackingPolicy(
        rules=rules
    )

    auto_fix_decision = (
        auto_fix_policy.execute(
            auto_fix_context
        )
    )

    assert auto_fix_decision.passed
    assert auto_fix_decision.has_violations
    assert auto_fix_decision.has_auto_fix

    assert auto_fix_decision.sanitized_reply == (
        "สอบถามรายละเอียด"
        "ผ่านช่องทางนี้ร้านได้เลยค่ะ"
    )

    assert auto_fix_context.sanitized_reply == (
        auto_fix_decision
        .sanitized_reply
    )

    assert auto_fix_policy.events == [
        "can_execute",
        "before_execute",
        "evaluate",
        "auto_fix",
        "after_execute",
    ]

    # --------------------------------------------------
    # Disabled Rule ต้องไม่ทำงาน
    # --------------------------------------------------

    disabled_rule_context = PolicyContext(
        original_reply=(
            "ข้อความต้องห้าม"
        ),
    )

    disabled_rule_decision = (
        policy.execute(
            disabled_rule_context
        )
    )

    assert disabled_rule_decision.passed

    assert not (
        disabled_rule_decision
        .has_violations
    )

    assert all(
        trace.rule_id != "TEST-999"
        for trace in (
            disabled_rule_decision.trace
        )
    )

    # --------------------------------------------------
    # Regex
    # --------------------------------------------------

    regex_rule = PolicyRule(
        rule_id="PRIVACY-001",
        name="Phone number",
        category=RuleCategory.PRIVACY,
        severity=Severity.HIGH,
        description=(
            "ตรวจหมายเลขโทรศัพท์"
        ),
        patterns=(
            r"0\d{8,9}",
        ),
        pattern_type=PatternType.REGEX,
        action=PolicyAction.BLOCK,
        priority=100,
    )

    regex_policy = TrackingPolicy(
        rules=(
            regex_rule,
        )
    )

    regex_context = PolicyContext(
        original_reply=(
            "ติดต่อได้ที่ 0812345678 ค่ะ"
        ),
    )

    regex_decision = regex_policy.execute(
        regex_context
    )

    assert not regex_decision.passed

    assert regex_decision.violations[
        0
    ].matched_text == "0812345678"

    # --------------------------------------------------
    # Invalid Regex ต้องถูกจับโดย execute()
    # --------------------------------------------------

    invalid_regex_rule = PolicyRule(
        rule_id="TEST-REGEX-001",
        name="Invalid regex",
        category=RuleCategory.QUALITY,
        severity=Severity.HIGH,
        description=(
            "Regex สำหรับทดสอบ Error"
        ),
        patterns=(
            "[",
        ),
        pattern_type=PatternType.REGEX,
        action=PolicyAction.BLOCK,
    )

    invalid_regex_policy = TrackingPolicy(
        rules=(
            invalid_regex_rule,
        )
    )

    invalid_regex_context = PolicyContext(
        original_reply="ทดสอบ",
    )

    invalid_regex_decision = (
        invalid_regex_policy.execute(
            invalid_regex_context
        )
    )

    assert not invalid_regex_decision.passed

    assert (
        invalid_regex_decision
        .requires_human_review
    )

    assert "execution_error" in (
        invalid_regex_decision.metadata
    )

    assert "ValueError" in (
        invalid_regex_decision.metadata[
            "execution_error"
        ]
    )

    # --------------------------------------------------
    # Platform-specific can_execute
    # --------------------------------------------------

    platform_policy = PlatformOnlyPolicy(
        name="shopee_only",
        rules=rules,
    )

    line_context = PolicyContext(
        original_reply=(
            "โอนเข้าบัญชีได้เลยค่ะ"
        ),
        platform="line",
    )

    line_decision = (
        platform_policy.execute(
            line_context
        )
    )

    assert line_decision.passed

    assert line_decision.metadata[
        "executed"
    ] is False

    shopee_platform_context = PolicyContext(
        original_reply=(
            "โอนเข้าบัญชีได้เลยค่ะ"
        ),
        platform="shopee",
    )

    shopee_platform_decision = (
        platform_policy.execute(
            shopee_platform_context
        )
    )

    assert not (
        shopee_platform_decision.passed
    )

    # --------------------------------------------------
    # Exception Handling
    # --------------------------------------------------

    broken_policy = BrokenPolicy(
        name="broken_policy",
    )

    broken_context = PolicyContext(
        original_reply="ทดสอบ",
    )

    broken_decision = broken_policy.execute(
        broken_context
    )

    assert not broken_decision.passed

    assert (
        broken_decision
        .requires_human_review
    )

    assert "execution_error" in (
        broken_decision.metadata
    )

    assert "RuntimeError" in (
        broken_decision.metadata[
            "execution_error"
        ]
    )

    assert broken_decision.warnings

    # --------------------------------------------------
    # Regression: คำสั้นไม่ควรชนคำอื่น
    # --------------------------------------------------
    # BasePolicy ปัจจุบันใช้ substring matching
    # จึงยังต้องหลีกเลี่ยง Keyword กว้าง เช่น "รับ"
    # Test นี้บันทึกพฤติกรรมที่ปลอดภัยด้วยคำเต็ม

    safe_keyword_rule = PolicyRule(
        rule_id="REGRESSION-001",
        name="Explicit buying phrase",
        category=RuleCategory.QUALITY,
        severity=Severity.LOW,
        description=(
            "ตรวจคำสั่งซื้อแบบคำเต็ม"
        ),
        patterns=(
            "รับสินค้า",
        ),
        action=PolicyAction.WARN,
    )

    safe_keyword_policy = TrackingPolicy(
        rules=(
            safe_keyword_rule,
        )
    )

    false_positive_context = PolicyContext(
        original_reply="ขอบคุณครับ",
    )

    false_positive_decision = (
        safe_keyword_policy.execute(
            false_positive_context
        )
    )

    assert not (
        false_positive_decision
        .has_violations
    )

    true_positive_context = PolicyContext(
        original_reply=(
            "ต้องการรับสินค้าพรุ่งนี้"
        ),
    )

    true_positive_decision = (
        safe_keyword_policy.execute(
            true_positive_context
        )
    )

    assert (
        true_positive_decision
        .has_violations
    )

    # --------------------------------------------------
    # Print Result
    # --------------------------------------------------

    print("=" * 60)
    print(
        "Base Policy "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Safe:",
        safe_decision.passed,
        safe_decision.risk_score,
    )

    print(
        "Warning:",
        warning_decision.passed,
        warning_decision.risk_score,
    )

    print(
        "Block:",
        block_decision.passed,
        block_decision.risk_score,
    )

    print(
        "Auto Fix:",
        auto_fix_decision.has_auto_fix,
        auto_fix_decision.sanitized_reply,
    )

    print(
        "Regex:",
        regex_decision.passed,
        regex_decision.violations[
            0
        ].matched_text,
    )

    print(
        "Broken:",
        broken_decision.passed,
        broken_decision.requires_human_review,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()