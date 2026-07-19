"""ทดสอบ Data Models ของ Sales Intelligence Layer."""

from app.core.customer_intent_score import (
    CustomerIntentScore,
    CustomerStage,
)
from app.core.sales_context import (
    CustomerPersonaResult,
    CustomerPersonaType,
    DecisionRecord,
    EmotionResult,
    EmotionType,
    SalesAction,
    SalesContext,
    SalesPipelineStage,
    SalesStrategy,
)


def main() -> None:
    """ตรวจ SalesContext, SalesStrategy และ DecisionRecord."""

    # --------------------------------------------------
    # EmotionResult
    # --------------------------------------------------

    neutral_emotion = EmotionResult()

    assert neutral_emotion.emotion == (
        EmotionType.NEUTRAL
    )

    assert neutral_emotion.score == 0

    assert not (
        neutral_emotion.is_negative_signal
    )

    price_resistance = EmotionResult(
        emotion=EmotionType.PRICE_RESISTANCE,
        score=82,
        matched_keywords=[
            "แพง",
            "มีถูกกว่านี้ไหม",
        ],
        reason=(
            "ลูกค้ามีข้อกังวลเรื่องราคา"
        ),
    )

    assert (
        price_resistance.is_negative_signal
    )

    confused_emotion = EmotionResult(
        emotion=EmotionType.CONFUSED,
        score=70,
    )

    assert (
        confused_emotion.is_negative_signal
    )

    # --------------------------------------------------
    # CustomerPersonaResult
    # --------------------------------------------------

    persona_result = CustomerPersonaResult(
        persona=(
            CustomerPersonaType.BAKERY_OWNER
        ),
        confidence=85,
        matched_keywords=[
            "ร้านเบเกอรี่",
            "ขายขนม",
        ],
        reason=(
            "ลูกค้าระบุว่าเปิดร้านเบเกอรี่"
        ),
    )

    assert persona_result.persona == (
        CustomerPersonaType.BAKERY_OWNER
    )

    assert persona_result.confidence == 85

    assert "ร้านเบเกอรี่" in (
        persona_result.matched_keywords
    )

    # --------------------------------------------------
    # SalesStrategy
    # --------------------------------------------------

    default_strategy = SalesStrategy()

    assert default_strategy.pipeline_stage == (
        SalesPipelineStage.INFORMATION
    )

    assert default_strategy.primary_action == (
        SalesAction.ANSWER
    )

    assert not (
        default_strategy.can_sell_proactively
    )

    selling_strategy = SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.RECOMMENDATION
        ),
        primary_action=(
            SalesAction.RECOMMEND
        ),
        sales_confidence=78,
        response_tone=(
            "เป็นกันเองและช่วยตัดสินใจ"
        ),
        response_goal=(
            "แนะนำสินค้าที่เหมาะสม"
        ),
        should_recommend=True,
        should_cross_sell=True,
        reason=(
            "ลูกค้าแสดงความสนใจสินค้า"
        ),
    )

    assert (
        selling_strategy.can_sell_proactively
    )

    assert selling_strategy.should_recommend
    assert selling_strategy.should_cross_sell

    handoff_strategy = SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.OBJECTION
        ),
        primary_action=(
            SalesAction.HUMAN_HANDOFF
        ),
        sales_confidence=90,
        should_handoff=True,
        reason=(
            "ลูกค้าขอราคาพิเศษ"
        ),
    )

    assert not (
        handoff_strategy.can_sell_proactively
    )

    # --------------------------------------------------
    # DecisionRecord
    # --------------------------------------------------

    decision_record = DecisionRecord(
        original_message=(
            "อยากทำบราวนี่ขาย"
        ),
        enriched_message=(
            "อยากทำบราวนี่ขาย"
        ),
        customer_stage="interested",
        intent_score=63,
        emotion="interested",
        emotion_score=70,
        persona="bakery_owner",
        persona_confidence=85,
        pipeline_stage="recommendation",
        primary_action="recommend",
        sales_confidence=78,
        recommendations=[
            "กล่องบราวนี่",
            "ถุงซีล",
        ],
        human_handoff=False,
        metadata={
            "channel": "test",
        },
    )

    decision_record.add_reason(
        "ลูกค้าต้องการทำสินค้าเพื่อขาย"
    )

    decision_record.add_reason(
        "ลูกค้าต้องการทำสินค้าเพื่อขาย"
    )

    decision_record.add_reason(
        "   "
    )

    assert decision_record.reasons == [
        "ลูกค้าต้องการทำสินค้าเพื่อขาย"
    ]

    decision_dict = (
        decision_record.to_dict()
    )

    assert decision_dict[
        "original_message"
    ] == "อยากทำบราวนี่ขาย"

    assert decision_dict[
        "sales_confidence"
    ] == 78

    assert decision_dict[
        "recommendations"
    ] == [
        "กล่องบราวนี่",
        "ถุงซีล",
    ]

    assert decision_dict[
        "metadata"
    ] == {
        "channel": "test",
    }

    # ต้องเป็นสำเนา ไม่ใช่ List ตัวเดิม
    copied_recommendations = (
        decision_dict["recommendations"]
    )

    copied_recommendations.append(
        "สติ๊กเกอร์"
    )

    assert decision_record.recommendations == [
        "กล่องบราวนี่",
        "ถุงซีล",
    ]

    # --------------------------------------------------
    # Default SalesContext
    # --------------------------------------------------

    default_context = SalesContext()

    assert default_context.original_message == ""
    assert default_context.enriched_message == ""

    assert (
        default_context.customer_intent.stage
        == CustomerStage.INFORMATION
    )

    assert (
        default_context.customer_intent.score
        == 0
    )

    assert default_context.emotion.emotion == (
        EmotionType.NEUTRAL
    )

    assert default_context.persona.persona == (
        CustomerPersonaType.UNKNOWN
    )

    assert default_context.sales_confidence == 0

    assert not default_context.should_handoff

    # --------------------------------------------------
    # Complete SalesContext
    # --------------------------------------------------

    customer_intent = CustomerIntentScore(
        stage=CustomerStage.INTERESTED,
        score=63,
        matched_keywords=[
            "สนใจ",
            "มีสีอะไร",
        ],
        reason=(
            "ลูกค้าแสดงความสนใจสินค้า"
        ),
    )

    emotion = EmotionResult(
        emotion=EmotionType.INTERESTED,
        score=72,
        matched_keywords=[
            "สนใจ",
        ],
        reason=(
            "ข้อความแสดงความสนใจ"
        ),
    )

    context = SalesContext(
        original_message=(
            "สนใจถ้วยคัพเค้กรุ่น 5040"
        ),
        enriched_message=(
            "สนใจถ้วยคัพเค้กรุ่น 5040"
        ),
        customer_intent=customer_intent,
        emotion=emotion,
        persona=persona_result,
        strategy=selling_strategy,
        recommendation_keywords=[
            "กล่องคัพเค้ก",
            "สติ๊กเกอร์",
        ],
    )

    assert context.sales_confidence == 78
    assert not context.should_handoff

    context.update_decision_record()

    record = context.decision_record

    assert record.original_message == (
        "สนใจถ้วยคัพเค้กรุ่น 5040"
    )

    assert record.customer_stage == (
        "interested"
    )

    assert record.intent_score == 63

    assert record.emotion == "interested"

    assert record.persona == (
        "bakery_owner"
    )

    assert record.pipeline_stage == (
        "recommendation"
    )

    assert record.primary_action == (
        "recommend"
    )

    assert record.sales_confidence == 78

    assert record.recommendations == [
        "กล่องคัพเค้ก",
        "สติ๊กเกอร์",
    ]

    assert not record.human_handoff

    assert (
        customer_intent.reason
        in record.reasons
    )

    assert (
        emotion.reason
        in record.reasons
    )

    assert (
        persona_result.reason
        in record.reasons
    )

    assert (
        selling_strategy.reason
        in record.reasons
    )

    # เรียกซ้ำแล้วเหตุผลต้องไม่ซ้ำ
    reason_count = len(
        record.reasons
    )

    context.update_decision_record()

    assert len(
        record.reasons
    ) == reason_count

    # --------------------------------------------------
    # SalesContext.to_dict()
    # --------------------------------------------------

    context_dict = context.to_dict()

    assert context_dict[
        "original_message"
    ] == (
        "สนใจถ้วยคัพเค้กรุ่น 5040"
    )

    assert context_dict[
        "customer_intent"
    ]["stage"] == "interested"

    assert context_dict[
        "customer_intent"
    ]["score"] == 63

    assert context_dict[
        "emotion"
    ]["type"] == "interested"

    assert context_dict[
        "persona"
    ]["type"] == "bakery_owner"

    assert context_dict[
        "strategy"
    ]["pipeline_stage"] == (
        "recommendation"
    )

    assert context_dict[
        "strategy"
    ]["primary_action"] == (
        "recommend"
    )

    assert context_dict[
        "strategy"
    ]["should_cross_sell"]

    assert context_dict[
        "recommendation_keywords"
    ] == [
        "กล่องคัพเค้ก",
        "สติ๊กเกอร์",
    ]

    assert context_dict[
        "decision_record"
    ]["sales_confidence"] == 78

    # --------------------------------------------------
    # Handoff Context
    # --------------------------------------------------

    handoff_context = SalesContext(
        original_message=(
            "ขอราคาพิเศษสำหรับ 1,000 ชิ้น"
        ),
        strategy=handoff_strategy,
    )

    assert handoff_context.should_handoff

    handoff_context.update_decision_record()

    assert (
        handoff_context.decision_record
        .human_handoff
    )

    print("=" * 60)
    print(
        "Sales Context "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Customer Stage:",
        record.customer_stage,
    )

    print(
        "Emotion:",
        record.emotion,
        record.emotion_score,
    )

    print(
        "Persona:",
        record.persona,
        record.persona_confidence,
    )

    print(
        "Pipeline:",
        record.pipeline_stage,
    )

    print(
        "Action:",
        record.primary_action,
    )

    print(
        "Sales Confidence:",
        record.sales_confidence,
    )

    print(
        "Recommendations:",
        record.recommendations,
    )

    print(
        "Reasons:",
        record.reasons,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()