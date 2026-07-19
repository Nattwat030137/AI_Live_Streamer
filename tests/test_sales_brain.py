"""ทดสอบ Sales Brain."""

from app.core.sales_brain import (
    CROSS_SELL_RULES,
    SalesBrain,
    SalesSuggestion,
)
from app.core.search_executor import (
    SearchExecutionResult,
)
from app.search_planner import SearchPlan


def create_search_result() -> SearchExecutionResult:
    """สร้างผลค้นหาจำลองสำหรับใช้ทดสอบ."""

    return SearchExecutionResult(
        message="ทำบราวนี่",
        search_plan=SearchPlan(
            original_query="ทำบราวนี่"
        ),
        products=[
            {
                "product_name": (
                    "พิมพ์อบบราวนี่"
                ),
                "sku": "BROWNIE-PAN",
            }
        ],
        summary={
            "count": 1,
        },
        searched_keywords=[
            "บราวนี่",
        ],
    )


def main() -> None:
    """ตรวจการทำงานหลักของ Sales Brain."""

    search_result = create_search_result()

    brain = SalesBrain(
        limit=3
    )

    assert brain.detect_trigger(
        "มีถ้วยคัพเค้กไหม"
    ) == "คัพเค้ก"

    assert brain.detect_trigger(
        "อยากทำบราวนี่ขาย"
    ) == "บราวนี่"

    assert brain.detect_trigger(
        "ต้องการห่อคุกกี้"
    ) == "คุกกี้"

    assert brain.detect_trigger(
        "สอบถามการจัดส่ง"
    ) == ""

    suggestion = brain.suggest(
        message="อยากทำบราวนี่ขาย",
        search_result=search_result,
    )

    assert isinstance(
        suggestion,
        SalesSuggestion,
    )

    assert suggestion.has_result

    assert suggestion.trigger == (
        "บราวนี่"
    )

    assert suggestion.reason == (
        "Cross Sell Rule"
    )

    assert len(
        suggestion.keywords
    ) == 3

    assert suggestion.keywords == (
        CROSS_SELL_RULES["บราวนี่"][:3]
    )

    limited_brain = SalesBrain(
        limit=2
    )

    limited_suggestion = (
        limited_brain.suggest(
            message="มีถ้วยคัพเค้กไหม",
            search_result=search_result,
        )
    )

    assert limited_suggestion.has_result

    assert len(
        limited_suggestion.keywords
    ) == 2

    assert limited_suggestion.keywords == (
        CROSS_SELL_RULES["คัพเค้ก"][:2]
    )

    empty_suggestion = brain.suggest(
        message="สอบถามการจัดส่ง",
        search_result=search_result,
    )

    assert isinstance(
        empty_suggestion,
        SalesSuggestion,
    )

    assert not (
        empty_suggestion.has_result
    )

    assert (
        empty_suggestion.trigger
        == ""
    )

    assert (
        empty_suggestion.keywords
        == []
    )

    zero_limit_brain = SalesBrain(
        limit=0
    )

    zero_limit_suggestion = (
        zero_limit_brain.suggest(
            message="ห่อคุกกี้",
            search_result=search_result,
        )
    )

    assert not (
        zero_limit_suggestion.has_result
    )

    assert (
        zero_limit_suggestion.keywords
        == []
    )

    print("=" * 60)
    print(
        "Sales Brain "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Trigger:",
        suggestion.trigger,
    )

    print(
        "Keywords:",
        suggestion.keywords,
    )

    print(
        "Limit 2:",
        limited_suggestion.keywords,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()