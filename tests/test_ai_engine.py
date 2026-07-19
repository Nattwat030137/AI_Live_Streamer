"""ทดสอบ AI Engine พร้อม Context และ Sales Recommendation."""

from __future__ import annotations

from typing import Any

import app.ai_engine as ai_engine
from app.core.recommendation_search import (
    RecommendationItem,
    RecommendationSearchResult,
)
from app.core.sales_brain import SalesSuggestion


class FakeResponseClient:
    """จำลอง OpenAI Response Client โดยไม่ยิง API จริง."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        *,
        instructions: str,
        conversation: list[dict[str, str]],
    ) -> str:
        """บันทึก Prompt และ Conversation แล้วคืนคำตอบจำลอง."""

        self.calls.append(
            {
                "instructions": instructions,
                "conversation": conversation,
            }
        )

        return (
            "มีค่ะ รุ่น 5040 มีสีขาวและน้ำตาล "
            "ทั้งแบบเคลือบและไม่เคลือบค่ะ"
        )


class FakeSalesBrain:
    """จำลอง Sales Brain ให้คืนคำแนะนำที่แน่นอน."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def suggest(
        self,
        message: str,
        search_result: Any,
    ) -> SalesSuggestion:
        """คืนคำแนะนำ Cross-sell สำหรับคัพเค้ก."""

        self.calls.append(
            {
                "message": message,
                "search_result": search_result,
            }
        )

        if "คัพเค้ก" not in message:
            return SalesSuggestion()

        return SalesSuggestion(
            trigger="คัพเค้ก",
            keywords=[
                "กล่องคัพเค้ก",
                "สติ๊กเกอร์",
            ],
            reason="Cross Sell Rule",
        )


class FakeRecommendationSearch:
    """จำลองการค้นสินค้าที่ Sales Brain แนะนำ."""

    def __init__(self) -> None:
        self.calls: list[SalesSuggestion] = []

    def search(
        self,
        suggestion: SalesSuggestion,
    ) -> RecommendationSearchResult:
        """คืนสินค้าจำลองที่พบจริง."""

        self.calls.append(
            suggestion
        )

        if not suggestion.has_result:
            return RecommendationSearchResult(
                source_trigger=suggestion.trigger,
            )

        return RecommendationSearchResult(
            source_trigger=suggestion.trigger,
            items=[
                RecommendationItem(
                    keyword="กล่องคัพเค้ก",
                    score=98,
                    products=[
                        {
                            "product_name": (
                                "กล่องคัพเค้ก "
                                "4 ช่องพร้อมฝา"
                            ),
                            "sku": "CUPCAKE-BOX-4",
                            "description": "-",
                        }
                    ],
                    summary={
                        "count": 1,
                    },
                ),
                RecommendationItem(
                    keyword="สติ๊กเกอร์",
                    score=87,
                    products=[
                        {
                            "product_name": (
                                "สติ๊กเกอร์ตกแต่ง"
                                "กล่องเบเกอรี่"
                            ),
                            "sku": "STICKER-BAKERY",
                            "description": "-",
                        }
                    ],
                    summary={
                        "count": 1,
                    },
                ),
            ],
        )


def main() -> None:
    """ตรวจ Orchestrator, Context, Sales Brain และ Memory."""

    original_response_client = (
        ai_engine.response_client
    )

    original_sales_brain = (
        ai_engine.sales_brain
    )

    original_recommendation_search = (
        ai_engine.recommendation_search
    )

    try:
        ai_engine.clear_memory()

        assert ai_engine.ask_ai(
            "   "
        ) == "กรุณาพิมพ์ข้อความก่อนนะคะ"

        assert not ai_engine.get_context()[
            "has_product_context"
        ]

        fake_response_client = (
            FakeResponseClient()
        )

        fake_sales_brain = (
            FakeSalesBrain()
        )

        fake_recommendation_search = (
            FakeRecommendationSearch()
        )

        ai_engine.response_client = (
            fake_response_client
        )

        ai_engine.sales_brain = (
            fake_sales_brain
        )

        ai_engine.recommendation_search = (
            fake_recommendation_search
        )

        # --------------------------------------------------
        # รอบที่ 1: ค้นสินค้าหลัก + Recommendation
        # --------------------------------------------------

        first_answer = ai_engine.ask_ai(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        )

        assert "รุ่น 5040" in first_answer

        assert len(
            fake_response_client.calls
        ) == 1

        assert len(
            fake_sales_brain.calls
        ) == 1

        assert len(
            fake_recommendation_search.calls
        ) == 1

        first_api_call = (
            fake_response_client.calls[0]
        )

        first_instructions = (
            first_api_call["instructions"]
        )

        assert (
            "ข้อมูลสินค้าแนะนำเพิ่มเติม"
            "ที่พบจริง"
            in first_instructions
        )

        assert (
            "กล่องคัพเค้ก"
            in first_instructions
        )

        assert (
            "กล่องคัพเค้ก 4 ช่องพร้อมฝา"
            in first_instructions
        )

        assert (
            "สติ๊กเกอร์"
            in first_instructions
        )

        assert (
            "แนะนำสินค้าเพิ่มเติม"
            "ไม่เกิน 2 รายการ"
            in first_instructions
        )

        assert first_api_call[
            "conversation"
        ][-1] == {
            "role": "user",
            "content": (
                "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
            ),
        }

        first_context = (
            ai_engine.get_context()
        )

        assert first_context[
            "has_product_context"
        ]

        assert first_context[
            "last_model"
        ] == "5040"

        # --------------------------------------------------
        # Preview Sales Recommendations
        # --------------------------------------------------

        preview = (
            ai_engine.preview_sales_recommendations(
                "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
            )
        )

        assert preview[
            "trigger"
        ] == "คัพเค้ก"

        assert preview[
            "suggested_keywords"
        ] == [
            "กล่องคัพเค้ก",
            "สติ๊กเกอร์",
        ]

        assert preview[
            "found_recommendations"
        ]

        assert preview[
            "total_product_count"
        ] == 2

        assert len(
            preview["top_items"]
        ) == 2

        assert preview[
            "top_items"
        ][0]["keyword"] == "กล่องคัพเค้ก"

        # Preview ต้องไม่บันทึก Memory
        assert len(
            ai_engine.get_memory_messages()
        ) == 2

        # --------------------------------------------------
        # รอบที่ 2: Context Follow-up
        # --------------------------------------------------

        second_answer = ai_engine.ask_ai(
            "แล้วสีขาวล่ะ"
        )

        assert "รุ่น 5040" in second_answer

        assert len(
            fake_response_client.calls
        ) == 2

        second_api_call = (
            fake_response_client.calls[1]
        )

        assert (
            "รุ่น 5040 แล้วสีขาวล่ะ"
            in second_api_call["instructions"]
        )

        # Conversation ต้องเก็บข้อความจริง
        assert second_api_call[
            "conversation"
        ][-1] == {
            "role": "user",
            "content": "แล้วสีขาวล่ะ",
        }

        # --------------------------------------------------
        # รอบที่ 3: Direct Answer เรื่องราคา
        # --------------------------------------------------

        price_answer = ai_engine.ask_ai(
            "ราคาเท่าไร"
        )

        assert "รุ่น 5040" in price_answer
        assert "แอดมิน" in price_answer

        # Direct Answer ไม่ควรเรียก OpenAI เพิ่ม
        assert len(
            fake_response_client.calls
        ) == 2

        # --------------------------------------------------
        # Memory
        # --------------------------------------------------

        messages = (
            ai_engine.get_memory_messages()
        )

        assert len(messages) == 6

        assert messages[0] == {
            "role": "user",
            "content": (
                "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
            ),
        }

        assert messages[2] == {
            "role": "user",
            "content": "แล้วสีขาวล่ะ",
        }

        assert messages[4] == {
            "role": "user",
            "content": "ราคาเท่าไร",
        }

        # --------------------------------------------------
        # Clear
        # --------------------------------------------------

        ai_engine.clear_memory()

        assert (
            ai_engine.get_memory_messages()
            == []
        )

        assert not ai_engine.get_context()[
            "has_product_context"
        ]

        print("=" * 60)
        print(
            "AI Engine + Sales Recommendation "
            "ผ่านการทดสอบทั้งหมด"
        )
        print("=" * 60)

        print(
            "First:",
            first_answer,
        )

        print(
            "Follow-up:",
            second_answer,
        )

        print(
            "Price:",
            price_answer,
        )

        print(
            "Recommendation:",
            preview["top_items"],
        )

        print(
            "OpenAI calls:",
            len(
                fake_response_client.calls
            ),
        )

        print("=" * 60)

    finally:
        ai_engine.response_client = (
            original_response_client
        )

        ai_engine.sales_brain = (
            original_sales_brain
        )

        ai_engine.recommendation_search = (
            original_recommendation_search
        )

        ai_engine.clear_memory()


if __name__ == "__main__":
    main()