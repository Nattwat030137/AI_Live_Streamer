"""ทดสอบ Data Models ของ AI Governance Framework."""

from __future__ import annotations

from app.policies.models import (
    PatternType,
    PlatformProfile,
    PolicyAction,
    PolicyExample,
    PolicyResult,
    PolicyRule,
    PolicyTraceEntry,
    PolicyViolation,
    RuleCategory,
    Severity,
)


def assert_raises_value_error(
    factory,
    expected_text: str,
) -> None:
    """ตรวจว่า Callable ต้องเกิด ValueError ตามข้อความที่กำหนด."""

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


def main() -> None:
    """ตรวจ Models, Validation และค่าที่คำนวณได้."""

    # --------------------------------------------------
    # Enums
    # --------------------------------------------------

    assert RuleCategory.BUSINESS.value == (
        "business"
    )

    assert Severity.CRITICAL.value == (
        "critical"
    )

    assert PolicyAction.AUTO_FIX.value == (
        "auto_fix"
    )

    assert PatternType.REGEX.value == (
        "regex"
    )

    # --------------------------------------------------
    # PolicyExample
    # --------------------------------------------------

    good_example = PolicyExample(
        text=(
            "สามารถดำเนินการผ่าน"
            "ช่องทางที่แพลตฟอร์มรองรับได้ค่ะ"
        ),
        description=(
            "ข้อความที่อยู่ภายในแพลตฟอร์ม"
        ),
    )

    assert good_example.text
    assert good_example.description

    assert_raises_value_error(
        lambda: PolicyExample(
            text="   "
        ),
        "PolicyExample.text",
    )

    # --------------------------------------------------
    # PolicyRule
    # --------------------------------------------------

    warning_rule = PolicyRule(
        rule_id="BUSINESS-001",
        name="Unknown price claim",
        category=RuleCategory.BUSINESS,
        severity=Severity.MEDIUM,
        description=(
            "ห้ามแจ้งราคาที่ไม่มีข้อมูลรองรับ"
        ),
        patterns=(
            "ราคาเพียง",
            "ลดเหลือ",
        ),
        pattern_type=PatternType.KEYWORD,
        action=PolicyAction.WARN,
        suggestion=(
            "ให้แอดมินตรวจสอบราคา"
        ),
        priority=80,
        version="1.0",
        tags=(
            "price",
            "accuracy",
        ),
        owner="business",
        good_examples=(
            PolicyExample(
                text=(
                    "ขออนุญาตให้แอดมิน"
                    "ตรวจสอบราคาล่าสุดค่ะ"
                ),
            ),
        ),
        bad_examples=(
            PolicyExample(
                text="ราคาพิเศษ 25 บาทค่ะ",
            ),
        ),
        metadata={
            "source": "business_policy",
        },
    )

    assert warning_rule.rule_id == (
        "BUSINESS-001"
    )

    assert warning_rule.risk_score == 30
    assert not warning_rule.is_blocking
    assert not warning_rule.requires_human_review

    warning_rule_dict = (
        warning_rule.to_dict()
    )

    assert warning_rule_dict[
        "category"
    ] == "business"

    assert warning_rule_dict[
        "severity"
    ] == "medium"

    assert warning_rule_dict[
        "action"
    ] == "warn"

    assert warning_rule_dict[
        "patterns"
    ] == [
        "ราคาเพียง",
        "ลดเหลือ",
    ]

    assert warning_rule_dict[
        "tags"
    ] == [
        "price",
        "accuracy",
    ]

    assert warning_rule_dict[
        "good_examples"
    ][0]["text"]

    assert warning_rule_dict[
        "metadata"
    ] == {
        "source": "business_policy",
    }

    block_rule = PolicyRule(
        rule_id="SHOPEE-001",
        name="External payment",
        category=RuleCategory.PLATFORM,
        severity=Severity.HIGH,
        description=(
            "ห้ามชักชวนให้ชำระเงิน"
            "นอกแพลตฟอร์ม"
        ),
        patterns=(
            "โอนเข้าบัญชี",
            "ชำระนอกระบบ",
        ),
        action=PolicyAction.BLOCK,
        priority=100,
    )

    assert block_rule.risk_score == 60
    assert block_rule.is_blocking
    assert not block_rule.requires_human_review

    handoff_rule = PolicyRule(
        rule_id="LEGAL-001",
        name="Legal review",
        category=RuleCategory.LEGAL,
        severity=Severity.CRITICAL,
        description=(
            "ข้อความนี้ต้องให้เจ้าหน้าที่ตรวจสอบ"
        ),
        patterns=(
            "รับประกันรักษาโรค",
        ),
        action=PolicyAction.HUMAN_HANDOFF,
        priority=120,
    )

    assert handoff_rule.risk_score == 100
    assert handoff_rule.is_blocking
    assert handoff_rule.requires_human_review

    auto_fix_rule = PolicyRule(
        rule_id="SHOPEE-002",
        name="External contact auto fix",
        category=RuleCategory.PLATFORM,
        severity=Severity.HIGH,
        description=(
            "ไม่ควรชักชวนลูกค้าไปยัง"
            "ช่องทางติดต่อภายนอก"
        ),
        patterns=(
            "แอดไลน์",
            "ทักไลน์",
        ),
        action=PolicyAction.AUTO_FIX,
        replacement_text=(
            "สามารถสอบถามรายละเอียดเพิ่มเติม"
            "ผ่านช่องทางนี้ได้ค่ะ"
        ),
        priority=95,
    )

    assert not auto_fix_rule.is_blocking
    assert auto_fix_rule.replacement_text

    # --------------------------------------------------
    # PolicyRule Validation
    # --------------------------------------------------

    assert_raises_value_error(
        lambda: PolicyRule(
            rule_id="",
            name="Invalid",
            category=RuleCategory.BUSINESS,
            severity=Severity.LOW,
            description="ทดสอบ",
        ),
        "rule_id",
    )

    assert_raises_value_error(
        lambda: PolicyRule(
            rule_id="TEST-001",
            name="   ",
            category=RuleCategory.BUSINESS,
            severity=Severity.LOW,
            description="ทดสอบ",
        ),
        "name",
    )

    assert_raises_value_error(
        lambda: PolicyRule(
            rule_id="TEST-002",
            name="Invalid description",
            category=RuleCategory.BUSINESS,
            severity=Severity.LOW,
            description="   ",
        ),
        "description",
    )

    assert_raises_value_error(
        lambda: PolicyRule(
            rule_id="TEST-003",
            name="Invalid priority",
            category=RuleCategory.BUSINESS,
            severity=Severity.LOW,
            description="ทดสอบ",
            priority=-1,
        ),
        "priority",
    )

    assert_raises_value_error(
        lambda: PolicyRule(
            rule_id="TEST-004",
            name="Missing replacement",
            category=RuleCategory.PLATFORM,
            severity=Severity.HIGH,
            description="ทดสอบ",
            action=PolicyAction.AUTO_FIX,
            replacement_text="   ",
        ),
        "replacement_text",
    )

    # --------------------------------------------------
    # PolicyViolation
    # --------------------------------------------------

    warning_violation = PolicyViolation(
        rule_id=warning_rule.rule_id,
        rule_name=warning_rule.name,
        category=warning_rule.category,
        severity=warning_rule.severity,
        action=warning_rule.action,
        matched_text="ลดเหลือ",
        message=(
            "พบข้อความราคาที่อาจไม่มีข้อมูลรองรับ"
        ),
        suggestion=warning_rule.suggestion,
        metadata={
            "position": 10,
        },
    )

    assert warning_violation.risk_score == 30
    assert not warning_violation.blocks_message
    assert not warning_violation.can_auto_fix
    assert not warning_violation.requires_human_review

    violation_dict = (
        warning_violation.to_dict()
    )

    assert violation_dict[
        "rule_id"
    ] == "BUSINESS-001"

    assert violation_dict[
        "risk_score"
    ] == 30

    assert not violation_dict[
        "blocks_message"
    ]

    block_violation = PolicyViolation(
        rule_id=block_rule.rule_id,
        rule_name=block_rule.name,
        category=block_rule.category,
        severity=block_rule.severity,
        action=block_rule.action,
        matched_text="โอนเข้าบัญชี",
        message=(
            "พบการชำระเงินนอกแพลตฟอร์ม"
        ),
    )

    assert block_violation.blocks_message
    assert not block_violation.can_auto_fix

    auto_fix_violation = PolicyViolation(
        rule_id=auto_fix_rule.rule_id,
        rule_name=auto_fix_rule.name,
        category=auto_fix_rule.category,
        severity=auto_fix_rule.severity,
        action=auto_fix_rule.action,
        matched_text="แอดไลน์",
        message=(
            "พบการชักชวนติดต่อภายนอก"
        ),
        replacement_text=(
            auto_fix_rule.replacement_text
        ),
    )

    assert auto_fix_violation.can_auto_fix
    assert not auto_fix_violation.blocks_message

    handoff_violation = PolicyViolation(
        rule_id=handoff_rule.rule_id,
        rule_name=handoff_rule.name,
        category=handoff_rule.category,
        severity=handoff_rule.severity,
        action=handoff_rule.action,
        matched_text="รับประกันรักษาโรค",
        message=(
            "ข้อความต้องให้เจ้าหน้าที่ตรวจสอบ"
        ),
    )

    assert handoff_violation.blocks_message
    assert handoff_violation.requires_human_review

    # --------------------------------------------------
    # PolicyTraceEntry
    # --------------------------------------------------

    trace_entry = PolicyTraceEntry(
        rule_id="BUSINESS-001",
        passed=False,
        action=PolicyAction.WARN,
        message="พบข้อความที่ตรงกับกฎ",
        execution_time_ms=1.25,
    )

    trace_dict = trace_entry.to_dict()

    assert trace_dict[
        "rule_id"
    ] == "BUSINESS-001"

    assert not trace_dict[
        "passed"
    ]

    assert trace_dict[
        "action"
    ] == "warn"

    assert trace_dict[
        "execution_time_ms"
    ] == 1.25

    # --------------------------------------------------
    # PolicyResult
    # --------------------------------------------------

    result = PolicyResult(
        original_reply=(
            "ลดเหลือ 25 บาท "
            "โอนเข้าบัญชีได้เลยค่ะ"
        ),
        sanitized_reply=(
            "ขออนุญาตให้แอดมิน"
            "ตรวจสอบรายละเอียดค่ะ"
        ),
        platform="shopee",
        policy_version="1.0",
    )

    assert result.allowed
    assert result.compliance_score == 100
    assert result.risk_score == 0
    assert not result.has_violations
    assert not result.has_critical_violation

    result.add_violation(
        warning_violation
    )

    assert result.has_violations
    assert result.allowed
    assert result.risk_score == 30
    assert result.compliance_score == 70

    result.add_violation(
        block_violation
    )

    assert not result.allowed
    assert result.risk_score == 90
    assert result.compliance_score == 10

    assert result.blocked_rule_ids == [
        "SHOPEE-001",
    ]

    assert result.violation_categories == [
        RuleCategory.BUSINESS,
        RuleCategory.PLATFORM,
    ]

    result.add_warning(
        "ข้อความอาจต้องตรวจสอบเพิ่มเติม"
    )

    result.add_warning(
        "ข้อความอาจต้องตรวจสอบเพิ่มเติม"
    )

    result.add_warning(
        "   "
    )

    assert result.warnings == [
        "ข้อความอาจต้องตรวจสอบเพิ่มเติม"
    ]

    result.add_trace(
        trace_entry
    )

    assert len(result.trace) == 1

    result_dict = result.to_dict()

    assert result_dict[
        "platform"
    ] == "shopee"

    assert not result_dict[
        "allowed"
    ]

    assert result_dict[
        "risk_score"
    ] == 90

    assert result_dict[
        "compliance_score"
    ] == 10

    assert result_dict[
        "blocked_rule_ids"
    ] == [
        "SHOPEE-001",
    ]

    assert result_dict[
        "violation_categories"
    ] == [
        "business",
        "platform",
    ]

    assert len(
        result_dict["violations"]
    ) == 2

    # --------------------------------------------------
    # Critical PolicyResult
    # --------------------------------------------------

    critical_result = PolicyResult(
        original_reply=(
            "สินค้านี้รับประกันรักษาโรคได้"
        ),
        sanitized_reply="",
        platform="website",
    )

    critical_result.add_violation(
        handoff_violation
    )

    assert not critical_result.allowed
    assert critical_result.risk_score == 100
    assert critical_result.compliance_score == 0
    assert critical_result.has_critical_violation
    assert critical_result.requires_human_review

    assert critical_result.blocked_rule_ids == [
        "LEGAL-001",
    ]

    # Risk Score ต้องไม่เกิน 100
    critical_result.add_violation(
        block_violation
    )

    assert critical_result.risk_score == 100
    assert critical_result.compliance_score == 0

    # --------------------------------------------------
    # PlatformProfile
    # --------------------------------------------------

    disabled_rule = PolicyRule(
        rule_id="SHOPEE-003",
        name="Disabled test rule",
        category=RuleCategory.PLATFORM,
        severity=Severity.LOW,
        description="กฎทดสอบที่ปิดใช้งาน",
        action=PolicyAction.WARN,
        enabled=False,
        priority=200,
    )

    profile = PlatformProfile(
        platform_name="shopee",
        version="2026.07",
        description=(
            "Policy Profile สำหรับ Shopee"
        ),
        rules=(
            warning_rule,
            block_rule,
            disabled_rule,
            auto_fix_rule,
        ),
        enabled=True,
        max_reply_length=500,
        default_tone=(
            "สุภาพ กระชับ และชัดเจน"
        ),
        metadata={
            "region": "thailand",
        },
    )

    assert profile.platform_name == (
        "shopee"
    )

    assert profile.enabled
    assert profile.max_reply_length == 500

    enabled_rules = profile.enabled_rules

    assert len(enabled_rules) == 3

    assert enabled_rules[0].rule_id == (
        "SHOPEE-001"
    )

    assert enabled_rules[1].rule_id == (
        "SHOPEE-002"
    )

    assert enabled_rules[2].rule_id == (
        "BUSINESS-001"
    )

    assert profile.get_rule(
        "SHOPEE-001"
    ) == block_rule

    assert profile.get_rule(
        "shopee-002"
    ) == auto_fix_rule

    assert profile.get_rule(
        "NOT-FOUND"
    ) is None

    profile_dict = profile.to_dict()

    assert profile_dict[
        "platform_name"
    ] == "shopee"

    assert profile_dict[
        "version"
    ] == "2026.07"

    assert len(
        profile_dict["rules"]
    ) == 4

    assert profile_dict[
        "metadata"
    ] == {
        "region": "thailand",
    }

    # --------------------------------------------------
    # PlatformProfile Validation
    # --------------------------------------------------

    assert_raises_value_error(
        lambda: PlatformProfile(
            platform_name="   ",
            version="1.0",
        ),
        "platform_name",
    )

    assert_raises_value_error(
        lambda: PlatformProfile(
            platform_name="shopee",
            version="   ",
        ),
        "version",
    )

    assert_raises_value_error(
        lambda: PlatformProfile(
            platform_name="shopee",
            version="1.0",
            max_reply_length=0,
        ),
        "max_reply_length",
    )

    print("=" * 60)
    print(
        "Policy Models "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Warning Rule:",
        warning_rule.rule_id,
        warning_rule.risk_score,
    )

    print(
        "Block Rule:",
        block_rule.rule_id,
        block_rule.risk_score,
    )

    print(
        "Result:",
        (
            f"allowed={result.allowed}, "
            f"risk={result.risk_score}, "
            f"compliance="
            f"{result.compliance_score}"
        ),
    )

    print(
        "Critical:",
        (
            f"allowed="
            f"{critical_result.allowed}, "
            f"human_review="
            f"{critical_result.requires_human_review}"
        ),
    )

    print(
        "Enabled Rules:",
        [
            rule.rule_id
            for rule
            in enabled_rules
        ],
    )

    print("=" * 60)


if __name__ == "__main__":
    main()