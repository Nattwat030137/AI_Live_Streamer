"""AI Engine orchestrator พร้อม Context และ Sales Brain."""

from __future__ import annotations

from typing import Any

from app.conversation_memory import ConversationMemory
from app.core.answer_builder import AnswerBuilder
from app.core.context_engine import ContextEngine
from app.core.openai_client import AIResponseClient
from app.core.prompt_builder import PromptBuilder
from app.core.recommendation_search import (
    RecommendationSearch,
    RecommendationSearchResult,
)
from app.core.sales_brain import (
    SalesBrain,
    SalesSuggestion,
)
from app.core.search_executor import (
    SearchExecutionResult,
    SearchExecutor,
)
from app.intent_engine import Intent, detect_intent
from app.knowledge_engine import load_all_knowledge


MEMORY_LIMIT = 10

memory = ConversationMemory(
    max_messages=MEMORY_LIMIT,
)

search_executor = SearchExecutor()
prompt_builder = PromptBuilder()
answer_builder = AnswerBuilder()
response_client = AIResponseClient()
context_engine = ContextEngine()
sales_brain = SalesBrain(
    limit=3
)
recommendation_search = RecommendationSearch(
    keyword_limit=3,
    product_limit_per_keyword=5,
    result_limit=2,
)


STATIC_INTENTS = {
    Intent.SHIPPING,
    Intent.STORE,
    Intent.CATEGORY,
}


def save_to_memory(
    user_message: str,
    assistant_message: str,
) -> None:
    """บันทึกข้อความจริงของผู้ใช้และคำตอบลง Memory."""

    memory.add_user_message(
        user_message
    )

    memory.add_assistant_message(
        assistant_message
    )


def build_conversation(
    original_message: str,
) -> list[dict[str, str]]:
    """
    สร้าง Conversation สำหรับ OpenAI.

    ใช้ข้อความต้นฉบับของลูกค้า
    ไม่ใช้ข้อความที่ Context Engine เติมแล้ว
    """

    conversation = memory.get_messages()

    conversation.append(
        {
            "role": "user",
            "content": original_message,
        }
    )

    return conversation


def get_search_result(
    message: str,
    intent: Intent,
) -> SearchExecutionResult:
    """ค้นสินค้าเฉพาะ Intent ที่ต้องใช้ Search Layer."""

    if intent in STATIC_INTENTS:
        return search_executor.search(
            ""
        )

    return search_executor.search(
        message
    )


def build_direct_answer(
    *,
    intent: Intent,
    search_result: SearchExecutionResult,
    knowledge: dict[str, Any],
) -> str | None:
    """สร้างคำตอบสำเร็จรูปโดยไม่เรียก OpenAI."""

    return answer_builder.build(
        intent=intent,
        search_result=search_result,
        knowledge=knowledge,
    )


def build_sales_suggestion(
    *,
    message: str,
    search_result: SearchExecutionResult,
) -> SalesSuggestion:
    """วิเคราะห์คำแนะนำ Cross-sell จากข้อความลูกค้า."""

    return sales_brain.suggest(
        message=message,
        search_result=search_result,
    )


def get_recommendation_result(
    suggestion: SalesSuggestion,
) -> RecommendationSearchResult:
    """ค้นสินค้าจริงจากคำแนะนำของ Sales Brain."""

    return recommendation_search.search(
        suggestion
    )


def build_ai_answer(
    *,
    original_message: str,
    search_result: SearchExecutionResult,
    recommendation_result: RecommendationSearchResult,
) -> str:
    """สร้าง Prompt พร้อมสินค้าแนะนำ แล้วเรียก OpenAI."""

    instructions = prompt_builder.build(
        search_result=search_result,
        recommendation_result=(
            recommendation_result
        ),
    )

    conversation = build_conversation(
        original_message
    )

    return response_client.generate(
        instructions=instructions,
        conversation=conversation,
    )


def ask_ai(message: str) -> str:
    """
    วิเคราะห์ Context, Intent, สินค้าหลัก และสินค้าแนะนำ.

    ข้อความต้นฉบับ:
        ใช้บันทึกใน Memory และส่งเป็น Conversation

    ข้อความที่เติม Context:
        ใช้ตรวจ Intent ค้นสินค้าหลัก
        และวิเคราะห์คำแนะนำการขาย
    """

    original_message = message.strip()

    if not original_message:
        return "กรุณาพิมพ์ข้อความก่อนนะคะ"

    enriched_message = context_engine.enrich(
        original_message
    )

    intent = detect_intent(
        enriched_message
    )

    knowledge = load_all_knowledge()

    search_result = get_search_result(
        message=enriched_message,
        intent=intent,
    )

    if search_result.found_products:
        context_engine.update(
            user_message=original_message,
            search_result=search_result,
        )

    answer = build_direct_answer(
        intent=intent,
        search_result=search_result,
        knowledge=knowledge,
    )

    if answer is None:
        suggestion = build_sales_suggestion(
            message=enriched_message,
            search_result=search_result,
        )

        recommendation_result = (
            get_recommendation_result(
                suggestion
            )
        )

        answer = build_ai_answer(
            original_message=original_message,
            search_result=search_result,
            recommendation_result=(
                recommendation_result
            ),
        )

    save_to_memory(
        user_message=original_message,
        assistant_message=answer,
    )

    return answer


def clear_memory() -> None:
    """ล้าง Conversation Memory และ Product Context."""

    memory.clear()
    context_engine.clear()


def get_memory_messages() -> list[dict[str, str]]:
    """คืนสำเนาข้อความทั้งหมดใน Memory."""

    return memory.get_messages()


def get_context() -> dict[str, Any]:
    """คืนข้อมูล Context ปัจจุบันสำหรับ Developer Mode."""

    context = context_engine.context

    return {
        "last_user_message": (
            context.last_user_message
        ),
        "last_model": (
            context.last_model
        ),
        "last_product_name": (
            context.last_product_name
        ),
        "last_keywords": list(
            context.last_keywords
        ),
        "last_summary": dict(
            context.last_summary
        ),
        "has_product_context": (
            context.has_product_context
        ),
    }


def preview_sales_recommendations(
    message: str,
) -> dict[str, Any]:
    """
    แสดงผล Sales Brain และ Recommendation Search.

    ใช้สำหรับ Developer Mode โดยไม่เรียก OpenAI
    และไม่บันทึกข้อความลง Memory
    """

    cleaned_message = message.strip()

    if not cleaned_message:
        return {
            "message": "",
            "enriched_message": "",
            "trigger": "",
            "suggested_keywords": [],
            "found_recommendations": False,
            "total_product_count": 0,
            "top_items": [],
        }

    enriched_message = context_engine.enrich(
        cleaned_message
    )

    intent = detect_intent(
        enriched_message
    )

    search_result = get_search_result(
        message=enriched_message,
        intent=intent,
    )

    suggestion = build_sales_suggestion(
        message=enriched_message,
        search_result=search_result,
    )

    recommendation_result = (
        get_recommendation_result(
            suggestion
        )
    )

    top_items = (
        recommendation_result.top_items(
            limit=2
        )
    )

    return {
        "message": cleaned_message,
        "enriched_message": (
            enriched_message
        ),
        "trigger": suggestion.trigger,
        "suggested_keywords": list(
            suggestion.keywords
        ),
        "found_recommendations": (
            recommendation_result
            .found_recommendations
        ),
        "total_product_count": (
            recommendation_result
            .total_product_count
        ),
        "top_items": [
            {
                "keyword": item.keyword,
                "score": item.score,
                "product_count": (
                    item.product_count
                ),
            }
            for item in top_items
        ],
    }


if __name__ == "__main__":
    print(
        "AI Engine พร้อม Context และ Sales Brain"
    )