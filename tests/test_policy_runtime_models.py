"""ทดสอบ Runtime Models ของ AI Governance Framework."""

from __future__ import annotations

from app.policies.models import (
    PolicyAction,
    PolicyTraceEntry,
    PolicyViolation,
    RuleCategory,
    Severity,
)
from app.policies.runtime_models import (
    PolicyContext,
    PolicyDecision,
    clamp_score,
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


def create_warning_violation(
) -> PolicyViolation:
    """สร้าง Violation แบบ Warning."""

    return PolicyViolation(
        rule_id="BUSINESS-001",
        rule_name="Unknown price claim",
        category=RuleCategory.BUSINESS,
        severity=Severity.MEDIUM,
        action=PolicyAction.WARN,
        matched_text="ลดเหลือ",
        message=(
            "พบข้อความราคาที่อาจ"
            "ไม่มีข้อมูลรองรับ"
        ),
        suggestion=(
            "ขอให้แอดมินตรวจสอบราคา"
        ),
    )


def create_block_violation(
) -> PolicyViolation:
    """สร้าง Violation แบบ Block."""

    return PolicyViolation(
        rule_id="SHOPEE-001",
        rule_name="External payment",
        category=RuleCategory.PLATFORM,
        severity=Severity.HIGH,
        action=PolicyAction.BLOCK,
        matched_text="โอนเข้าบัญชี",
        message=(
            "พบการชำระเงินนอกแพลตฟอร์ม"
        ),
    )


def create_handoff_violation(
) -> PolicyViolation:
    """สร้าง Violation แบบ Human Handoff."""

    return PolicyViolation(
        rule_id="LEGAL-001",
        rule_name="Legal review",
        category=RuleCategory.LEGAL,
        severity=Severity.CRITICAL,
        action=PolicyAction.HUMAN_HANDOFF,
        matched_text=(
            "รับประกันรักษาโรค"
        ),
        message=(
            "ต้องให้เจ้าหน้าที่ตรวจสอบ"
        ),
    )


def create_auto_fix_violation(
) -> PolicyViolation:
    """สร้าง Violation แบบ Auto Fix."""

    return PolicyViolation(
        rule_id="SHOPEE-002",
        rule_name="External contact",
        category=RuleCategory.PLATFORM,
        severity=Severity.HIGH,
        action=PolicyAction.AUTO_FIX,
        matched_text="แอดไลน์",
        message=(
            "พบการชักชวนติดต่อภายนอก"
        ),
        replacement_text=(
            "สามารถสอบถามรายละเอียด"
            "เพิ่มเติมผ่านช่องทางนี้ได้ค่ะ"
        ),
    )


def main() -> None:
    """ตรวจ PolicyContext และ PolicyDecision."""

    # --------------------------------------------------
    # clamp_score
    # --------------------------------------------------

    assert clamp_score(-20) == 0
    assert clamp_score(0) == 0
    assert clamp_score(45) == 45
    assert clamp_score(100) == 100
    assert clamp_score(150) == 100

    # รองรับค่าที่แปลงเป็น int ได้
    assert clamp_score(72.9) == 72
    assert clamp_score("55") == 55

    # --------------------------------------------------
    # PolicyContext Defaults
    # --------------------------------------------------

    default_context = PolicyContext(
        original_reply=(
            "  สวัสดีค่ะ  "
        ),
    )

    assert default_context.original_reply == (
        "สวัสดีค่ะ"
    )

    assert default_context.platform == (
        "generic"
    )

    assert default_context.sanitized_reply == (
        "สวัสดีค่ะ"
    )

    assert default_context.effective_reply == (
        "สวัสดีค่ะ"
    )

    assert default_context.has_reply

    assert not (
        default_context
        .requires_low_confidence_review
    )

    # --------------------------------------------------
    # Platform Normalization
    # --------------------------------------------------

    shopee_context = PolicyContext(
        original_reply=(
            "สินค้าพร้อมให้สอบถามค่ะ"
        ),
        platform="  SHOPEE  ",
    )

    assert shopee_context.platform == (
        "shopee"
    )

    blank_platform_context = PolicyContext(
        original_reply="ทดสอบ",
        platform="   ",
    )

    assert blank_platform_context.platform == (
        "generic"
    )

    # --------------------------------------------------
    # Score Clamping
    # --------------------------------------------------

    score_context = PolicyContext(
        original_reply="ทดสอบคะแนน",
        intent_score=-10,
        emotion_score=120,
        persona_confidence=80,
        sales_confidence=105,
        knowledge_confidence=-1,
    )

    assert score_context.intent_score == 0
    assert score_context.emotion_score == 100

    assert (
        score_context.persona_confidence
        == 80
    )

    assert (
        score_context.sales_confidence
        == 100
    )

    assert (
        score_context.knowledge_confidence
        == 0
    )

    # --------------------------------------------------
    # Low Confidence Review
    # --------------------------------------------------

    low_knowledge_context = PolicyContext(
        original_reply=(
            "ราคาสินค้า 25 บาทค่ะ"
        ),
        sales_confidence=85,
        knowledge_confidence=30,
    )

    assert (
        low_knowledge_context
        .requires_low_confidence_review
    )

    low_sales_context = PolicyContext(
        original_reply="ทดสอบ",
        sales_confidence=35,
        knowledge_confidence=90,
    )

    assert (
        low_sales_context
        .requires_low_confidence_review
    )

    safe_confidence_context = PolicyContext(
        original_reply="ทดสอบ",
        sales_confidence=70,
        knowledge_confidence=80,
    )

    assert not (
        safe_confidence_context
        .requires_low_confidence_review
    )

    zero_confidence_context = PolicyContext(
        original_reply="ทดสอบ",
        sales_confidence=0,
        knowledge_confidence=0,
    )

    # คะแนน 0 หมายถึงยังไม่มีข้อมูล
    # จึงยังไม่ถือว่า Low Confidence
    assert not (
        zero_confidence_context
        .requires_low_confidence_review
    )

    mixed_zero_context = PolicyContext(
        original_reply="ทดสอบ",
        sales_confidence=0,
        knowledge_confidence=25,
    )

    assert (
        mixed_zero_context
        .requires_low_confidence_review
    )

    # --------------------------------------------------
    # Sanitized Reply
    # --------------------------------------------------

    update_context = PolicyContext(
        original_reply=(
            "แอดไลน์ร้านได้เลยค่ะ"
        ),
    )

    update_context.update_sanitized_reply(
        "  สามารถสอบถามผ่าน"
        "ช่องทางนี้ได้ค่ะ  "
    )

    assert update_context.sanitized_reply == (
        "สามารถสอบถามผ่าน"
        "ช่องทางนี้ได้ค่ะ"
    )

    assert update_context.effective_reply == (
        "สามารถสอบถามผ่าน"
        "ช่องทางนี้ได้ค่ะ"
    )

    update_context.update_sanitized_reply(
        "   "
    )

    assert update_context.sanitized_reply == ""

    assert update_context.effective_reply == (
        update_context.original_reply
    )

    # --------------------------------------------------
    # Empty Reply
    # --------------------------------------------------

    empty_context = PolicyContext(
        original_reply="   ",
    )

    assert empty_context.original_reply == ""
    assert empty_context.sanitized_reply == ""
    assert empty_context.effective_reply == ""
    assert not empty_context.has_reply

    # --------------------------------------------------
    # PolicyContext.to_dict()
    # --------------------------------------------------

    complete_context = PolicyContext(
        original_reply=(
            "มีถ้วยคัพเค้กรุ่น 5040 ค่ะ"
        ),
        platform="Shopee",
        customer_message=(
            "มีรุ่น 5040 ไหม"
        ),
        customer_intent="interested",
        emotion="interested",
        persona="bakery_owner",
        pipeline_stage="recommendation",
        primary_action="recommend",
        intent_score=63,
        emotion_score=75,
        persona_confidence=82,
        sales_confidence=68,
        knowledge_confidence=90,
        recommendation_keywords=[
            "กล่องคัพเค้ก",
            "สติ๊กเกอร์",
        ],
        metadata={
            "channel_message_id": "TEST-001",
        },
    )

    context_dict = complete_context.to_dict()

    assert context_dict[
        "platform"
    ] == "shopee"

    assert context_dict[
        "customer_intent"
    ] == "interested"

    assert context_dict[
        "emotion"
    ] == "interested"

    assert context_dict[
        "persona"
    ] == "bakery_owner"

    assert context_dict[
        "sales_confidence"
    ] == 68

    assert context_dict[
        "knowledge_confidence"
    ] == 90

    assert context_dict[
        "recommendation_keywords"
    ] == [
        "กล่องคัพเค้ก",
        "สติ๊กเกอร์",
    ]

    assert not context_dict[
        "requires_low_confidence_review"
    ]

    assert context_dict[
        "metadata"
    ] == {
        "channel_message_id": "TEST-001",
    }

    # ต้องคืนสำเนาของ List
    copied_keywords = context_dict[
        "recommendation_keywords"
    ]

    copied_keywords.append(
        "ถุงซีล"
    )

    assert complete_context.recommendation_keywords == [
        "กล่องคัพเค้ก",
        "สติ๊กเกอร์",
    ]

    # --------------------------------------------------
    # PolicyDecision Defaults
    # --------------------------------------------------

    default_decision = PolicyDecision(
        policy_name="business_policy",
        original_reply=(
            "ขอให้แอดมินตรวจสอบราคาค่ะ"
        ),
    )

    assert default_decision.policy_name == (
        "business_policy"
    )

    assert default_decision.passed
    assert not default_decision.has_violations

    assert not (
        default_decision
        .has_blocking_violation
    )

    assert not default_decision.has_auto_fix
    assert default_decision.risk_score == 0

    assert not (
        default_decision
        .requires_human_review
    )

    assert (
        default_decision.execution_time_ms
        == 0.0
    )

    # --------------------------------------------------
    # PolicyDecision Validation
    # --------------------------------------------------

    assert_raises_value_error(
        lambda: PolicyDecision(
            policy_name="   "
        ),
        "policy_name",
    )

    negative_time_decision = PolicyDecision(
        policy_name="test_policy",
        execution_time_ms=-10,
    )

    assert (
        negative_time_decision
        .execution_time_ms
        == 0.0
    )

    # --------------------------------------------------
    # Warning Violation
    # --------------------------------------------------

    warning_violation = (
        create_warning_violation()
    )

    warning_decision = PolicyDecision(
        policy_name="business_policy",
        original_reply=(
            "วันนี้ลดเหลือ 25 บาทค่ะ"
        ),
    )

    warning_decision.add_violation(
        warning_violation
    )

    assert warning_decision.has_violations
    assert warning_decision.passed

    assert not (
        warning_decision
        .has_blocking_violation
    )

    assert warning_decision.risk_score == 30

    # --------------------------------------------------
    # Blocking Violation
    # --------------------------------------------------

    block_violation = (
        create_block_violation()
    )

    block_decision = PolicyDecision(
        policy_name="shopee_policy",
        original_reply=(
            "โอนเข้าบัญชีได้เลยค่ะ"
        ),
    )

    block_decision.add_violation(
        block_violation
    )

    assert block_decision.has_violations
    assert not block_decision.passed

    assert (
        block_decision
        .has_blocking_violation
    )

    assert block_decision.risk_score == 60

    assert not (
        block_decision
        .requires_human_review
    )

    # --------------------------------------------------
    # Human Handoff Violation
    # --------------------------------------------------

    handoff_violation = (
        create_handoff_violation()
    )

    handoff_decision = PolicyDecision(
        policy_name="legal_policy",
        original_reply=(
            "สินค้านี้รับประกันรักษาโรคค่ะ"
        ),
    )

    handoff_decision.add_violation(
        handoff_violation
    )

    assert not handoff_decision.passed

    assert (
        handoff_decision
        .has_blocking_violation
    )

    assert (
        handoff_decision
        .requires_human_review
    )

    assert handoff_decision.risk_score == 100

    # --------------------------------------------------
    # Auto Fix
    # --------------------------------------------------

    auto_fix_violation = (
        create_auto_fix_violation()
    )

    auto_fix_decision = PolicyDecision(
        policy_name="shopee_policy",
        original_reply=(
            "แอดไลน์ร้านได้เลยค่ะ"
        ),
    )

    auto_fix_decision.add_violation(
        auto_fix_violation
    )

    auto_fix_decision.set_sanitized_reply(
        auto_fix_violation
        .replacement_text
    )

    assert auto_fix_decision.passed
    assert auto_fix_decision.has_violations
    assert auto_fix_decision.has_auto_fix

    assert auto_fix_decision.sanitized_reply == (
        "สามารถสอบถามรายละเอียด"
        "เพิ่มเติมผ่านช่องทางนี้ได้ค่ะ"
    )

    assert auto_fix_decision.risk_score == 60

    # ข้อความเหมือนต้นฉบับ
    # ต้องไม่ถือว่าเป็น Auto Fix
    unchanged_decision = PolicyDecision(
        policy_name="test_policy",
        original_reply="ข้อความเดิม",
        sanitized_reply="ข้อความเดิม",
    )

    assert not unchanged_decision.has_auto_fix

    # --------------------------------------------------
    # Multiple Violations and Risk Cap
    # --------------------------------------------------

    combined_decision = PolicyDecision(
        policy_name="combined_policy",
        original_reply="ข้อความทดสอบ",
    )

    combined_decision.add_violation(
        warning_violation
    )

    combined_decision.add_violation(
        block_violation
    )

    combined_decision.add_violation(
        handoff_violation
    )

    assert combined_decision.risk_score == 100
    assert not combined_decision.passed

    assert (
        combined_decision
        .requires_human_review
    )

    # --------------------------------------------------
    # Warnings
    # --------------------------------------------------

    warning_decision.add_warning(
        "ควรตรวจสอบข้อมูลราคา"
    )

    warning_decision.add_warning(
        "ควรตรวจสอบข้อมูลราคา"
    )

    warning_decision.add_warning(
        "   "
    )

    assert warning_decision.warnings == [
        "ควรตรวจสอบข้อมูลราคา"
    ]

    # --------------------------------------------------
    # Trace
    # --------------------------------------------------

    trace_entry = PolicyTraceEntry(
        rule_id="BUSINESS-001",
        passed=False,
        action=PolicyAction.WARN,
        message=(
            "พบข้อความที่ตรงกับกฎ"
        ),
        execution_time_ms=1.5,
    )

    warning_decision.add_trace(
        trace_entry
    )

    assert len(
        warning_decision.trace
    ) == 1

    assert warning_decision.trace[
        0
    ] == trace_entry

    # --------------------------------------------------
    # refresh_status Regression
    # --------------------------------------------------

    manual_decision = PolicyDecision(
        policy_name="manual_policy",
        passed=True,
        violations=[
            block_violation,
        ],
    )

    # __post_init__ ต้องอัปเดต passed
    assert not manual_decision.passed

    assert (
        manual_decision
        .has_blocking_violation
    )

    # --------------------------------------------------
    # PolicyDecision.to_dict()
    # --------------------------------------------------

    decision_dict = (
        auto_fix_decision.to_dict()
    )

    assert decision_dict[
        "policy_name"
    ] == "shopee_policy"

    assert decision_dict[
        "passed"
    ]

    assert decision_dict[
        "has_violations"
    ]

    assert decision_dict[
        "has_auto_fix"
    ]

    assert decision_dict[
        "risk_score"
    ] == 60

    assert len(
        decision_dict["violations"]
    ) == 1

    assert decision_dict[
        "violations"
    ][0]["rule_id"] == "SHOPEE-002"

    # --------------------------------------------------
    # Regression: Results must return copies
    # --------------------------------------------------

    copied_warnings = decision_dict[
        "warnings"
    ]

    copied_warnings.append(
        "ข้อความใหม่"
    )

    assert (
        auto_fix_decision.warnings
        == []
    )

    # --------------------------------------------------
    # Print Result
    # --------------------------------------------------

    print("=" * 60)
    print(
        "Policy Runtime Models "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Context:",
        complete_context.platform,
        complete_context.sales_confidence,
        complete_context.knowledge_confidence,
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
        "Handoff:",
        handoff_decision.passed,
        handoff_decision.requires_human_review,
    )

    print(
        "Combined Risk:",
        combined_decision.risk_score,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()