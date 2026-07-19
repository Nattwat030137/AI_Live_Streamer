"""ทดสอบ Emotion Engine."""

from app.core.emotion_engine import (
    EmotionAnalysis,
    EmotionEngine,
    SentimentType,
    analyze_emotion,
    apply_emotion_analysis,
    build_emotion_reason,
    calculate_emotion_score,
    clamp_score,
    detect_text_intensity,
    determine_sentiment,
    find_emotion_matches,
)
from app.core.sales_context import (
    EmotionResult,
    EmotionType,
    SalesContext,
)


def main() -> None:
    """ตรวจการวิเคราะห์อารมณ์ทุกกรณีหลัก."""

    # --------------------------------------------------
    # clamp_score
    # --------------------------------------------------

    assert clamp_score(-10) == 0
    assert clamp_score(0) == 0
    assert clamp_score(55) == 55
    assert clamp_score(100) == 100
    assert clamp_score(150) == 100

    # --------------------------------------------------
    # find_emotion_matches
    # --------------------------------------------------

    positive_matches = find_emotion_matches(
        "ชอบมากเลยค่ะ สวยและถูกใจ",
        EmotionType.POSITIVE,
    )

    assert "ชอบ" in positive_matches
    assert "สวย" in positive_matches
    assert "ถูกใจ" in positive_matches

    assert find_emotion_matches(
        "   ",
        EmotionType.POSITIVE,
    ) == []

    # --------------------------------------------------
    # calculate_emotion_score
    # --------------------------------------------------

    assert calculate_emotion_score(
        emotion=EmotionType.POSITIVE,
        matches=[],
    ) == 0

    assert calculate_emotion_score(
        emotion=EmotionType.POSITIVE,
        matches=["ชอบ"],
    ) == 64

    assert calculate_emotion_score(
        emotion=EmotionType.POSITIVE,
        matches=["ชอบ", "สวย"],
    ) == 71

    assert calculate_emotion_score(
        emotion=EmotionType.NEGATIVE,
        matches=["แย่"],
        intensity_bonus=30,
    ) == 100

    # --------------------------------------------------
    # detect_text_intensity
    # --------------------------------------------------

    assert detect_text_intensity(
        ""
    ) == 0

    assert detect_text_intensity(
        "แพงจัง"
    ) == 0

    assert detect_text_intensity(
        "แพงมาก!!"
    ) == 8

    assert detect_text_intensity(
        "แพงมากๆ!!!"
    ) == 20

    assert detect_text_intensity(
        "ดีสุด ๆ!!!!"
    ) == 26

    # --------------------------------------------------
    # build_emotion_reason
    # --------------------------------------------------

    reason = build_emotion_reason(
        EmotionType.PRICE_RESISTANCE,
        [
            "แพง",
            "ลดได้ไหม",
        ],
    )

    assert "ข้อกังวลเรื่องราคา" in reason
    assert "แพง" in reason
    assert "ลดได้ไหม" in reason

    empty_reason = build_emotion_reason(
        EmotionType.NEUTRAL,
        [],
    )

    assert "ไม่พบคำ" in empty_reason

    # --------------------------------------------------
    # determine_sentiment
    # --------------------------------------------------

    assert determine_sentiment(
        EmotionType.POSITIVE
    ) == SentimentType.POSITIVE

    assert determine_sentiment(
        EmotionType.INTERESTED
    ) == SentimentType.POSITIVE

    assert determine_sentiment(
        EmotionType.NEGATIVE
    ) == SentimentType.NEGATIVE

    assert determine_sentiment(
        EmotionType.PRICE_RESISTANCE
    ) == SentimentType.NEGATIVE

    assert determine_sentiment(
        EmotionType.CONFUSED
    ) == SentimentType.NEGATIVE

    assert determine_sentiment(
        EmotionType.NEUTRAL
    ) == SentimentType.NEUTRAL

    # --------------------------------------------------
    # Positive
    # --------------------------------------------------

    positive_analysis = analyze_emotion(
        "ชอบมากค่ะ สวยและถูกใจ"
    )

    assert isinstance(
        positive_analysis,
        EmotionAnalysis,
    )

    assert positive_analysis.primary.emotion == (
        EmotionType.POSITIVE
    )

    assert positive_analysis.primary.score > 0

    assert positive_analysis.sentiment == (
        SentimentType.POSITIVE
    )

    assert "ชอบ" in (
        positive_analysis
        .primary
        .matched_keywords
    )

    # --------------------------------------------------
    # Interested
    # --------------------------------------------------

    interested_analysis = analyze_emotion(
        "สนใจรุ่นนี้ มีสีอะไรบ้าง"
    )

    assert interested_analysis.primary.emotion == (
        EmotionType.INTERESTED
    )

    assert interested_analysis.sentiment == (
        SentimentType.POSITIVE
    )

    assert "สนใจ" in (
        interested_analysis
        .primary
        .matched_keywords
    )

    # --------------------------------------------------
    # Hesitating
    # --------------------------------------------------

    hesitating_analysis = analyze_emotion(
        "ยังไม่แน่ใจ แบบนี้ดีไหมครับ"
    )

    assert hesitating_analysis.primary.emotion == (
        EmotionType.HESITATING
    )

    assert hesitating_analysis.sentiment == (
        SentimentType.NEGATIVE
    )

    assert hesitating_analysis.primary.score > 0

    # --------------------------------------------------
    # Price Resistance
    # --------------------------------------------------

    price_analysis = analyze_emotion(
        "แพงจัง มีถูกกว่านี้ไหม"
    )

    assert price_analysis.primary.emotion == (
        EmotionType.PRICE_RESISTANCE
    )

    assert price_analysis.sentiment == (
        SentimentType.NEGATIVE
    )

    assert price_analysis.primary.score >= 74

    assert "แพง" in (
        price_analysis
        .primary
        .matched_keywords
    )

    # --------------------------------------------------
    # Negative
    # --------------------------------------------------

    negative_analysis = analyze_emotion(
        "ไม่พอใจเลยค่ะ สินค้าแย่มาก"
    )

    assert negative_analysis.primary.emotion == (
        EmotionType.NEGATIVE
    )

    assert negative_analysis.sentiment == (
        SentimentType.NEGATIVE
    )

    assert negative_analysis.primary.score >= 80

    # --------------------------------------------------
    # Confused
    # --------------------------------------------------

    confused_analysis = analyze_emotion(
        "งงมาก ไม่เข้าใจว่าต่างกันยังไง"
    )

    assert confused_analysis.primary.emotion == (
        EmotionType.CONFUSED
    )

    assert confused_analysis.sentiment == (
        SentimentType.NEGATIVE
    )

    assert confused_analysis.primary.score >= 70

    # --------------------------------------------------
    # Secondary Emotion
    # --------------------------------------------------

    mixed_analysis = analyze_emotion(
        "แพงจัง แต่ก็ชอบและสนใจนะ"
    )

    assert mixed_analysis.primary.emotion == (
        EmotionType.PRICE_RESISTANCE
    )

    assert mixed_analysis.has_secondary

    assert mixed_analysis.secondary in {
        EmotionType.POSITIVE,
        EmotionType.INTERESTED,
    }

    # --------------------------------------------------
    # Neutral
    # --------------------------------------------------

    neutral_analysis = analyze_emotion(
        "สวัสดีครับ"
    )

    assert neutral_analysis.primary.emotion == (
        EmotionType.NEUTRAL
    )

    assert neutral_analysis.primary.score == 0

    assert neutral_analysis.sentiment == (
        SentimentType.NEUTRAL
    )

    assert not neutral_analysis.has_secondary

    # --------------------------------------------------
    # Empty Message
    # --------------------------------------------------

    empty_analysis = analyze_emotion(
        "   "
    )

    assert empty_analysis.primary.emotion == (
        EmotionType.NEUTRAL
    )

    assert empty_analysis.primary.score == 0
    assert empty_analysis.intensity == 0

    assert "ไม่มีข้อความ" in (
        empty_analysis.primary.reason
    )

    # --------------------------------------------------
    # Intensity affects score
    # --------------------------------------------------

    normal_price = analyze_emotion(
        "แพง"
    )

    intense_price = analyze_emotion(
        "แพงมากๆ!!!"
    )

    assert (
        intense_price.primary.score
        > normal_price.primary.score
    )

    assert (
        intense_price.intensity
        > normal_price.intensity
    )

    # --------------------------------------------------
    # apply_emotion_analysis
    # --------------------------------------------------

    context = SalesContext(
        original_message=(
            "แพงจัง มีถูกกว่านี้ไหม"
        ),
        enriched_message=(
            "แพงจัง มีถูกกว่านี้ไหม"
        ),
    )

    returned_context = (
        apply_emotion_analysis(
            context=context,
            analysis=price_analysis,
        )
    )

    assert returned_context is context

    assert context.emotion.emotion == (
        EmotionType.PRICE_RESISTANCE
    )

    assert context.emotion.score == (
        price_analysis.primary.score
    )

    assert context.decision_record.emotion == (
        "price_resistance"
    )

    assert context.decision_record.emotion_score == (
        price_analysis.primary.score
    )

    assert (
        price_analysis.primary.reason
        in context.decision_record.reasons
    )

    # --------------------------------------------------
    # Invalid Context
    # --------------------------------------------------

    class InvalidContext:
        pass

    try:
        apply_emotion_analysis(
            context=InvalidContext(),
            analysis=price_analysis,
        )

    except AttributeError as error:
        assert "emotion" in str(
            error
        )

    else:
        raise AssertionError(
            "ควรเกิด AttributeError "
            "เมื่อ Context ไม่มี emotion"
        )

    # --------------------------------------------------
    # EmotionEngine Facade
    # --------------------------------------------------

    engine = EmotionEngine()

    facade_analysis = engine.analyze(
        "สนใจมากค่ะ ชอบเลย"
    )

    assert facade_analysis.primary.emotion in {
        EmotionType.INTERESTED,
        EmotionType.POSITIVE,
    }

    facade_context = SalesContext(
        original_message=(
            "ไม่เข้าใจว่ารุ่นนี้ใช้ยังไง"
        ),
        enriched_message=(
            "ไม่เข้าใจว่ารุ่นนี้ใช้ยังไง"
        ),
    )

    applied_facade_context = engine.apply(
        context=facade_context,
        message=(
            "ไม่เข้าใจว่ารุ่นนี้ใช้ยังไง"
        ),
    )

    assert applied_facade_context is (
        facade_context
    )

    assert facade_context.emotion.emotion == (
        EmotionType.CONFUSED
    )

    assert facade_context.emotion.score > 0

    # --------------------------------------------------
    # EmotionResult behavior
    # --------------------------------------------------

    result = EmotionResult(
        emotion=EmotionType.NEGATIVE,
        score=90,
        matched_keywords=[
            "ไม่พอใจ",
        ],
        reason=(
            "ลูกค้ามีความรู้สึกเชิงลบ"
        ),
    )

    assert result.is_negative_signal

    positive_result = EmotionResult(
        emotion=EmotionType.POSITIVE,
        score=80,
    )

    assert not (
        positive_result.is_negative_signal
    )

    print("=" * 60)
    print(
        "Emotion Engine "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Positive:",
        positive_analysis.primary.emotion.value,
        positive_analysis.primary.score,
        positive_analysis.sentiment.value,
    )

    print(
        "Interested:",
        interested_analysis.primary.emotion.value,
        interested_analysis.primary.score,
        interested_analysis.sentiment.value,
    )

    print(
        "Hesitating:",
        hesitating_analysis.primary.emotion.value,
        hesitating_analysis.primary.score,
        hesitating_analysis.sentiment.value,
    )

    print(
        "Price Resistance:",
        price_analysis.primary.emotion.value,
        price_analysis.primary.score,
        price_analysis.sentiment.value,
    )

    print(
        "Negative:",
        negative_analysis.primary.emotion.value,
        negative_analysis.primary.score,
        negative_analysis.sentiment.value,
    )

    print(
        "Confused:",
        confused_analysis.primary.emotion.value,
        confused_analysis.primary.score,
        confused_analysis.sentiment.value,
    )

    print(
        "Mixed:",
        mixed_analysis.primary.emotion.value,
        "secondary=",
        (
            mixed_analysis.secondary.value
            if mixed_analysis.secondary
            else None
        ),
    )

    print("=" * 60)


if __name__ == "__main__":
    main()