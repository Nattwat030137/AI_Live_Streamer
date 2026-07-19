"""ทดสอบ Recommendation Search."""

from app.core.recommendation_search import (
    RecommendationItem,
    RecommendationSearch,
    RecommendationSearchResult,
    calculate_recommendation_score,
    format_recommendation_search,
    search_recommendation_keyword,
    search_sales_recommendations,
)
from app.core.sales_brain import SalesSuggestion


def main() -> None:
    """ตรวจฟังก์ชันหลักของ Recommendation Search."""

    # --------------------------------------------------
    # Score
    # --------------------------------------------------

    first_score = calculate_recommendation_score(
        position=0,
        product_count=5,
    )

    second_score = calculate_recommendation_score(
        position=1,
        product_count=3,
    )

    assert first_score == 100
    assert second_score == 88
    assert first_score > second_score

    assert calculate_recommendation_score(
        position=100,
        product_count=0,
    ) == 0

    # --------------------------------------------------
    # Recommendation Item
    # --------------------------------------------------

    item = RecommendationItem(
        keyword="กล่องบราวนี่",
        score=98,
        products=[
            {
                "product_name": (
                    "กล่องบราวนี่พร้อมฝา"
                ),
                "sku": "BOX-BROWNIE-01",
            },
            {
                "product_name": (
                    "กล่องบราวนี่คราฟท์"
                ),
                "sku": "BOX-BROWNIE-02",
            },
        ],
        summary={
            "count": 2,
        },
    )

    assert item.product_count == 2
    assert item.found_products

    empty_item = RecommendationItem(
        keyword="ไม่มีจริง",
        score=50,
    )

    assert empty_item.product_count == 0
    assert not empty_item.found_products

    # --------------------------------------------------
    # Recommendation Search Result
    # --------------------------------------------------

    result = RecommendationSearchResult(
        source_trigger="บราวนี่",
        items=[
            item,
            RecommendationItem(
                keyword="ถุงซีล",
                score=90,
                products=[
                    {
                        "product_name": (
                            "ถุงซีลใส"
                        ),
                        "sku": "SEAL-BAG-01",
                    }
                ],
                summary={
                    "count": 1,
                },
            ),
            empty_item,
        ],
    )

    assert result.found_recommendations
    assert result.total_product_count == 3

    top_items = result.top_items(
        limit=2
    )

    assert len(top_items) == 2
    assert top_items[0].keyword == (
        "กล่องบราวนี่"
    )
    assert top_items[1].keyword == (
        "ถุงซีล"
    )

    assert result.top_items(
        limit=0
    ) == []

    formatted = format_recommendation_search(
        result=result,
        item_limit=2,
        product_limit=1,
    )

    assert "บราวนี่" in formatted
    assert "กล่องบราวนี่" in formatted
    assert "ถุงซีล" in formatted
    assert "score=98" in formatted
    assert "กล่องบราวนี่พร้อมฝา" in formatted

    # --------------------------------------------------
    # Empty Suggestion
    # --------------------------------------------------

    empty_suggestion = SalesSuggestion()

    empty_result = search_sales_recommendations(
        suggestion=empty_suggestion,
    )

    assert not (
        empty_result.found_recommendations
    )

    assert empty_result.items == []

    # --------------------------------------------------
    # Real Database Search
    # --------------------------------------------------

    suggestion = SalesSuggestion(
        trigger="บราวนี่",
        keywords=[
            "กล่องบราวนี่",
            "ถุงซีล",
            "สติ๊กเกอร์",
        ],
        reason="Cross Sell Rule",
    )

    real_result = search_sales_recommendations(
        suggestion=suggestion,
        keyword_limit=3,
        product_limit_per_keyword=5,
    )

    assert real_result.source_trigger == (
        "บราวนี่"
    )

    assert len(
        real_result.items
    ) <= 3

    assert all(
        isinstance(
            recommendation_item,
            RecommendationItem,
        )
        for recommendation_item
        in real_result.items
    )

    assert all(
        recommendation_item.score >= 0
        for recommendation_item
        in real_result.items
    )

    real_top_items = real_result.top_items(
        limit=3
    )

    assert isinstance(
        real_top_items,
        list,
    )

    # --------------------------------------------------
    # Single Keyword Search
    # --------------------------------------------------

    keyword_item = (
        search_recommendation_keyword(
            keyword="กล่องบราวนี่",
            position=0,
            product_limit=5,
        )
    )

    assert keyword_item.keyword == (
        "กล่องบราวนี่"
    )

    assert keyword_item.score >= 95

    assert isinstance(
        keyword_item.products,
        list,
    )

    assert isinstance(
        keyword_item.summary,
        dict,
    )

    # ไม่บังคับว่าฐานข้อมูลจริงต้องพบคำนี้เสมอ
    if keyword_item.found_products:
        assert keyword_item.product_count > 0
    else:
        assert keyword_item.product_count == 0

    # --------------------------------------------------
    # Facade
    # --------------------------------------------------

    recommendation_search = (
        RecommendationSearch(
            keyword_limit=3,
            product_limit_per_keyword=5,
            result_limit=2,
        )
    )

    facade_result = (
        recommendation_search.search(
            suggestion
        )
    )

    assert facade_result.source_trigger == (
        "บราวนี่"
    )

    facade_text = (
        recommendation_search.format(
            facade_result
        )
    )

    assert isinstance(
        facade_text,
        str,
    )

    assert facade_text.strip()

    print("=" * 60)
    print(
        "Recommendation Search "
        "ผ่านการทดสอบทั้งหมด"
    )
    print("=" * 60)

    print(
        "Trigger:",
        real_result.source_trigger,
    )

    print(
        "จำนวนกลุ่ม:",
        len(real_result.items),
    )

    print(
        "จำนวนสินค้ารวม:",
        real_result.total_product_count,
    )

    print(
        "Top Keywords:",
        [
            recommendation_item.keyword
            for recommendation_item
            in real_top_items
        ],
    )

    print(
        "คำค้นเดี่ยวพบสินค้า:",
        keyword_item.found_products,
    )

    print("=" * 60)


if __name__ == "__main__":
    main()