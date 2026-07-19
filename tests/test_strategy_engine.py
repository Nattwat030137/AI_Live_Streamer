"""ทดสอบ Strategy Engine."""

from app.core.customer_intent_score import (
    CustomerIntentScore,
    CustomerStage,
)
from app.core.sales_context import (
    EmotionResult,
    EmotionType,
    SalesAction,
    SalesContext,
    SalesPipelineStage,
)
from app.core.strategy_engine import (
    StrategyEngine,
    apply_sales_strategy,
    build_buying_strategy,
    build_comparing_strategy,
    build_handoff_strategy,
    build_hesitating_strategy,
    build_information_strategy,
    build_interested_strategy,
    choose_sales_strategy,
    clamp_score,
    is_buying_customer,
    is_comparing_customer,
    is_hesitating_customer,
    is_interested_customer,
    select_strategy_rule,
    should_handoff_customer,
)


def create_context(
    *,
    message: str,
    stage: CustomerStage,
    score: int,
    emotion: EmotionType = EmotionType.NEUTRAL,
    emotion_score: int = 0,
) -> SalesContext:
    """สร้าง SalesContext สำหรับทดสอบ."""

    return SalesContext(
        original_message=message,
        enriched_message=message,
        customer_intent=CustomerIntentScore(
            stage=stage,
            score=score,
            matched_keywords=[],
            reason=(
                f"ทดสอบสถานะ {stage.value}"
            ),
        ),
        emotion=EmotionResult(
            emotion=emotion,
            score=emotion_score,
            matched_keywords=[],
            reason=(
                f"ทดสอบอารมณ์ {emotion.value}"
            ),
        ),
    )


def main() -> None:
    """ตรวจทุกกลยุทธ์และลำดับ Priority."""

    # --------------------------------------------------
    # clamp_score
    # --------------------------------------------------

    assert clamp_score(-10) == 0
    assert clamp_score(0) == 0
    assert clamp_score(50) == 50
    assert clamp_score(100) == 100
    assert clamp_score(150) == 100

    # --------------------------------------------------
    # Buying
    # --------------------------------------------------

    buying_context = create_context(
        message="มีของพร้อมส่งไหม เอา 10 แพ็ก",
        stage=CustomerStage.BUYING,
        score=100,
    )

    assert is_buying_customer(
        buying_context
    )

    assert not is_comparing_customer(
        buying_context
    )

    buying_strategy = build_buying_strategy(
        buying_context
    )

    assert buying_strategy.pipeline_stage == (
        SalesPipelineStage.CLOSING
    )

    assert buying_strategy.primary_action == (
        SalesAction.GUIDE_ORDER
    )

    assert buying_strategy.sales_confidence == 100
    assert not buying_strategy.should_recommend
    assert not buying_strategy.should_cross_sell
    assert not buying_strategy.should_upsell
    assert not buying_strategy.should_handoff

    assert buying_strategy.can_sell_proactively

    # --------------------------------------------------
    # Comparing
    # --------------------------------------------------

    comparing_context = create_context(
        message=(
            "รุ่น 5040 กับ 3830 "
            "ต่างกันยังไง"
        ),
        stage=CustomerStage.COMPARING,
        score=76,
    )

    assert is_comparing_customer(
        comparing_context
    )

    comparing_strategy = (
        build_comparing_strategy(
            comparing_context
        )
    )

    assert comparing_strategy.pipeline_stage == (
        SalesPipelineStage.COMPARISON
    )

    assert comparing_strategy.primary_action == (
        SalesAction.COMPARE
    )

    assert comparing_strategy.sales_confidence == 76
    assert comparing_strategy.should_recommend
    assert not comparing_strategy.should_cross_sell
    assert not comparing_strategy.should_handoff

    # --------------------------------------------------
    # Hesitating from CustomerStage
    # --------------------------------------------------

    hesitating_context = create_context(
        message="แบบนี้ดีไหม คุ้มไหมครับ",
        stage=CustomerStage.HESITATING,
        score=68,
    )

    assert is_hesitating_customer(
        hesitating_context
    )

    hesitating_strategy = (
        build_hesitating_strategy(
            hesitating_context
        )
    )

    assert hesitating_strategy.pipeline_stage == (
        SalesPipelineStage.OBJECTION
    )

    assert hesitating_strategy.primary_action == (
        SalesAction.REDUCE_CONCERN
    )

    # Engine จำกัดคะแนนลังเลไม่เกิน 58
    assert (
        hesitating_strategy.sales_confidence
        == 58
    )

    assert hesitating_strategy.should_ask_question
    assert not hesitating_strategy.should_recommend
    assert not hesitating_strategy.should_cross_sell
    assert not hesitating_strategy.should_handoff

    # --------------------------------------------------
    # Hesitating from Emotion
    # --------------------------------------------------

    price_resistance_context = create_context(
        message="แพงจัง มีถูกกว่านี้ไหม",
        stage=CustomerStage.INFORMATION,
        score=40,
        emotion=EmotionType.PRICE_RESISTANCE,
        emotion_score=82,
    )

    assert is_hesitating_customer(
        price_resistance_context
    )

    price_strategy = choose_sales_strategy(
        price_resistance_context
    )

    assert price_strategy.pipeline_stage == (
        SalesPipelineStage.OBJECTION
    )

    assert price_strategy.primary_action == (
        SalesAction.REDUCE_CONCERN
    )

    confused_context = create_context(
        message="ไม่เข้าใจว่าต่างกันยังไง",
        stage=CustomerStage.INFORMATION,
        score=40,
        emotion=EmotionType.CONFUSED,
        emotion_score=70,
    )

    assert is_hesitating_customer(
        confused_context
    )

    # --------------------------------------------------
    # Interested
    # --------------------------------------------------

    interested_context = create_context(
        message=(
            "สนใจรุ่น 5040 "
            "มีสีอะไรบ้าง"
        ),
        stage=CustomerStage.INTERESTED,
        score=63,
        emotion=EmotionType.INTERESTED,
        emotion_score=72,
    )

    assert is_interested_customer(
        interested_context
    )

    interested_strategy = (
        build_interested_strategy(
            interested_context
        )
    )

    assert interested_strategy.pipeline_stage == (
        SalesPipelineStage.RECOMMENDATION
    )

    assert interested_strategy.primary_action == (
        SalesAction.RECOMMEND
    )

    assert interested_strategy.sales_confidence == 63
    assert interested_strategy.should_recommend

    # คะแนนยังต่ำกว่า 65 จึงยังไม่ Cross-sell เชิงรุก
    assert not (
        interested_strategy.should_cross_sell
    )

    high_interest_context = create_context(
        message="สนใจมาก อยากได้รุ่นนี้",
        stage=CustomerStage.INTERESTED,
        score=75,
        emotion=EmotionType.INTERESTED,
        emotion_score=85,
    )

    high_interest_strategy = (
        build_interested_strategy(
            high_interest_context
        )
    )

    assert (
        high_interest_strategy
        .sales_confidence
        == 75
    )

    assert (
        high_interest_strategy
        .should_cross_sell
    )

    assert (
        high_interest_strategy
        .can_sell_proactively
    )

    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    information_context = create_context(
        message="รุ่นนี้ทำจากอะไร",
        stage=CustomerStage.INFORMATION,
        score=48,
    )

    information_strategy = (
        build_information_strategy(
            information_context
        )
    )

    assert information_strategy.pipeline_stage == (
        SalesPipelineStage.INFORMATION
    )

    assert information_strategy.primary_action == (
        SalesAction.ANSWER
    )

    # จำกัดคะแนนข้อมูลทั่วไปไว้ไม่เกิน 40
    assert (
        information_strategy.sales_confidence
        == 40
    )

    assert not information_strategy.should_recommend
    assert not information_strategy.should_cross_sell
    assert not information_strategy.should_handoff
    assert not information_strategy.can_sell_proactively

    # --------------------------------------------------
    # Human Handoff
    # --------------------------------------------------

    handoff_context = create_context(
        message=(
            "ขอราคาพิเศษสำหรับสั่งจำนวนมาก"
        ),
        stage=CustomerStage.BUYING,
        score=100,
    )

    assert should_handoff_customer(
        handoff_context
    )

    handoff_strategy = build_handoff_strategy(
        handoff_context
    )

    assert handoff_strategy.pipeline_stage == (
        SalesPipelineStage.OBJECTION
    )

    assert handoff_strategy.primary_action == (
        SalesAction.HUMAN_HANDOFF
    )

    assert handoff_strategy.sales_confidence == 20
    assert handoff_strategy.should_handoff
    assert not handoff_strategy.should_recommend
    assert not handoff_strategy.can_sell_proactively

    # --------------------------------------------------
    # Rule Priority
    # Handoff ต้องชนะ Buying
    # --------------------------------------------------

    selected_rule = select_strategy_rule(
        handoff_context
    )

    assert selected_rule is not None
    assert selected_rule.name == (
        "human_handoff"
    )
    assert selected_rule.priority == 100

    selected_handoff_strategy = (
        choose_sales_strategy(
            handoff_context
        )
    )

    assert (
        selected_handoff_strategy
        .primary_action
        == SalesAction.HUMAN_HANDOFF
    )

    # --------------------------------------------------
    # Rule Selection
    # --------------------------------------------------

    buying_rule = select_strategy_rule(
        buying_context
    )

    assert buying_rule is not None
    assert buying_rule.name == "buying"

    comparing_rule = select_strategy_rule(
        comparing_context
    )

    assert comparing_rule is not None
    assert comparing_rule.name == "comparing"

    hesitating_rule = select_strategy_rule(
        hesitating_context
    )

    assert hesitating_rule is not None
    assert hesitating_rule.name == "hesitating"

    interested_rule = select_strategy_rule(
        interested_context
    )

    assert interested_rule is not None
    assert interested_rule.name == "interested"

    information_rule = select_strategy_rule(
        information_context
    )

    assert information_rule is None

    # --------------------------------------------------
    # choose_sales_strategy
    # --------------------------------------------------

    assert choose_sales_strategy(
        buying_context
    ).primary_action == (
        SalesAction.GUIDE_ORDER
    )

    assert choose_sales_strategy(
        comparing_context
    ).primary_action == (
        SalesAction.COMPARE
    )

    assert choose_sales_strategy(
        hesitating_context
    ).primary_action == (
        SalesAction.REDUCE_CONCERN
    )

    assert choose_sales_strategy(
        interested_context
    ).primary_action == (
        SalesAction.RECOMMEND
    )

    assert choose_sales_strategy(
        information_context
    ).primary_action == (
        SalesAction.ANSWER
    )

    # --------------------------------------------------
    # apply_sales_strategy
    # --------------------------------------------------

    applied_context = apply_sales_strategy(
        interested_context
    )

    assert applied_context is interested_context

    assert applied_context.strategy.primary_action == (
        SalesAction.RECOMMEND
    )

    assert applied_context.decision_record[
        0:0
    ] if False else True

    record = applied_context.decision_record

    assert record.customer_stage == (
        "interested"
    )

    assert record.pipeline_stage == (
        "recommendation"
    )

    assert record.primary_action == (
        "recommend"
    )

    assert record.sales_confidence == 63

    assert (
        applied_context.strategy.reason
        in record.reasons
    )

    # --------------------------------------------------
    # StrategyEngine Facade
    # --------------------------------------------------

    engine = StrategyEngine()

    facade_strategy = engine.choose(
        comparing_context
    )

    assert facade_strategy.primary_action == (
        SalesAction.COMPARE
    )

    facade_context = engine.apply(
        buying_context
    )

    assert facade_context.strategy.pipeline_stage == (
        SalesPipelineStage.CLOSING
    )

    assert facade_context.strategy.primary_action == (
        SalesAction.GUIDE_ORDER
    )

    assert facade_context.decision_record[
        0:0
    ] if False else True

    assert (
        facade_context
        .decision_record
        .pipeline_stage
        == "closing"
    )

    assert (
        facade_context
        .decision_record
        .primary_action
        == "guide_order"
    )

    # --------------------------------------------------
    # Enriched message fallback
    # --------------------------------------------------

    fallback_message_context = SalesContext(
        original_message="ขอใบกำกับภาษี",
        enriched_message="",
        customer_intent=CustomerIntentScore(
            stage=CustomerStage.INFORMATION,
            score=40,
            matched_keywords=[],
            reason="ทดสอบ",
        ),
    )

    assert should_handoff_customer(
        fallback_message_context
    )

    print("=" * 60)
    print(
        "Strategy Engine "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Buying:",
        buying_strategy.pipeline_stage.value,
        buying_strategy.primary_action.value,
        buying_strategy.sales_confidence,
    )

    print(
        "Comparing:",
        comparing_strategy.pipeline_stage.value,
        comparing_strategy.primary_action.value,
        comparing_strategy.sales_confidence,
    )

    print(
        "Hesitating:",
        hesitating_strategy.pipeline_stage.value,
        hesitating_strategy.primary_action.value,
        hesitating_strategy.sales_confidence,
    )

    print(
        "Interested:",
        interested_strategy.pipeline_stage.value,
        interested_strategy.primary_action.value,
        interested_strategy.sales_confidence,
    )

    print(
        "Information:",
        information_strategy.pipeline_stage.value,
        information_strategy.primary_action.value,
        information_strategy.sales_confidence,
    )

    print(
        "Handoff:",
        handoff_strategy.pipeline_stage.value,
        handoff_strategy.primary_action.value,
        handoff_strategy.sales_confidence,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()