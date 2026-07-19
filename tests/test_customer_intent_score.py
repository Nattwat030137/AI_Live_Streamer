"""ทดสอบ Customer Intent Score."""

from app.core.customer_intent_score import (
    CustomerIntentAnalyzer,
    CustomerStage,
    analyze_customer_intent,
    calculate_stage_score,
    find_matches,
    get_sales_response_strategy,
)


def main() -> None:
    """ตรวจทุกสถานะและกลยุทธ์การตอบ."""

    # --------------------------------------------------
    # find_matches
    # --------------------------------------------------

    buying_matches = find_matches(
        "พร้อมสั่งซื้อและชำระเงินเลย",
        (
            "สั่งซื้อ",
            "ชำระเงิน",
        ),
    )

    assert buying_matches == [
        "สั่งซื้อ",
        "ชำระเงิน",
    ]

    assert find_matches(
        "   ",
        (
            "ซื้อ",
        ),
    ) == []

    # --------------------------------------------------
    # calculate_stage_score
    # --------------------------------------------------

    assert calculate_stage_score(
        matches=[],
        base_score=50,
    ) == 0

    assert calculate_stage_score(
        matches=[
            "ซื้อ",
        ],
        base_score=78,
    ) == 78

    assert calculate_stage_score(
        matches=[
            "ซื้อ",
            "สั่งเลย",
        ],
        base_score=78,
    ) == 86

    assert calculate_stage_score(
        matches=[
            "ซื้อ",
        ] * 10,
        base_score=78,
    ) == 100

    # --------------------------------------------------
    # BUYING
    # --------------------------------------------------

    buying_result = analyze_customer_intent(
        "มีของพร้อมส่งไหม ถ้ามีเอา 2 แพ็กครับ"
    )

    assert buying_result.stage == (
        CustomerStage.BUYING
    )

    assert buying_result.score >= 70

    assert buying_result.is_high_intent

    assert buying_result.matched_keywords

    assert (
        "เจตนาซื้อชัดเจน"
        in buying_result.reason
    )

    buying_strategy = (
        get_sales_response_strategy(
            buying_result
        )
    )

    assert "ขั้นตอนสั่งซื้อ" in (
        buying_strategy
    )

    # --------------------------------------------------
    # COMPARING
    # --------------------------------------------------

    comparing_result = (
        analyze_customer_intent(
            "รุ่น 5040 กับ 3830 "
            "ต่างกันยังไง ตัวไหนดี"
        )
    )

    assert comparing_result.stage == (
        CustomerStage.COMPARING
    )

    assert comparing_result.score > 0

    assert not (
        comparing_result.is_high_intent
    )

    assert (
        "เปรียบเทียบ"
        in comparing_result.reason
    )

    comparing_strategy = (
        get_sales_response_strategy(
            comparing_result
        )
    )

    assert (
        "ข้อแตกต่าง"
        in comparing_strategy
    )

    # --------------------------------------------------
    # HESITATING
    # --------------------------------------------------

    hesitating_result = (
        analyze_customer_intent(
            "แบบนี้ดีไหม คุ้มไหมครับ"
        )
    )

    assert hesitating_result.stage == (
        CustomerStage.HESITATING
    )

    assert hesitating_result.score > 0

    assert (
        "ลังเล"
        in hesitating_result.reason
        or "ข้อกังวล"
        in hesitating_result.reason
    )

    hesitating_strategy = (
        get_sales_response_strategy(
            hesitating_result
        )
    )

    assert (
        "ไม่กดดัน"
        in hesitating_strategy
    )

    # --------------------------------------------------
    # INTERESTED
    # --------------------------------------------------

    interested_result = (
        analyze_customer_intent(
            "สนใจรุ่น 5040 "
            "มีสีอะไรบ้าง"
        )
    )

    assert interested_result.stage == (
        CustomerStage.INTERESTED
    )

    assert interested_result.score > 0

    assert (
        "สนใจสินค้า"
        in interested_result.reason
    )

    interested_strategy = (
        get_sales_response_strategy(
            interested_result
        )
    )

    assert (
        "สินค้าเกี่ยวข้อง"
        in interested_strategy
    )

    # --------------------------------------------------
    # INFORMATION
    # --------------------------------------------------

    information_result = (
        analyze_customer_intent(
            "รุ่นนี้ทำจากอะไร "
            "และขนาดเท่าไร"
        )
    )

    assert information_result.stage == (
        CustomerStage.INFORMATION
    )

    assert information_result.score > 0

    assert (
        "สอบถามข้อมูล"
        in information_result.reason
    )

    information_strategy = (
        get_sales_response_strategy(
            information_result
        )
    )

    assert (
        "ตรงคำถาม"
        in information_strategy
    )

    # --------------------------------------------------
    # UNKNOWN MESSAGE
    # --------------------------------------------------

    unknown_result = (
        analyze_customer_intent(
            "สวัสดีครับ"
        )
    )

    assert unknown_result.stage == (
        CustomerStage.INFORMATION
    )

    assert unknown_result.score == 0

    assert unknown_result.matched_keywords == []

    # --------------------------------------------------
    # EMPTY MESSAGE
    # --------------------------------------------------

    empty_result = analyze_customer_intent(
        "   "
    )

    assert empty_result.stage == (
        CustomerStage.INFORMATION
    )

    assert empty_result.score == 0

    assert (
        "ไม่มีข้อความ"
        in empty_result.reason
    )

    # --------------------------------------------------
    # Facade
    # --------------------------------------------------

    analyzer = CustomerIntentAnalyzer()

    facade_result = analyzer.analyze(
        "อยากซื้อรุ่นนี้ สั่งเลยครับ"
    )

    assert facade_result.stage == (
        CustomerStage.BUYING
    )

    facade_strategy = analyzer.strategy(
        facade_result
    )

    assert isinstance(
        facade_strategy,
        str,
    )

    assert facade_strategy.strip()

    print("=" * 60)
    print(
        "Customer Intent Score "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Buying:",
        buying_result.stage.value,
        buying_result.score,
        buying_result.matched_keywords,
    )

    print(
        "Comparing:",
        comparing_result.stage.value,
        comparing_result.score,
        comparing_result.matched_keywords,
    )

    print(
        "Hesitating:",
        hesitating_result.stage.value,
        hesitating_result.score,
        hesitating_result.matched_keywords,
    )

    print(
        "Interested:",
        interested_result.stage.value,
        interested_result.score,
        interested_result.matched_keywords,
    )

    print(
        "Information:",
        information_result.stage.value,
        information_result.score,
        information_result.matched_keywords,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()