"""Prompt Builder สำหรับ AI Commerce OS."""

from __future__ import annotations

from dataclasses import dataclass
from multiprocessing import context
from typing import Any

from app.prompt import style
from app.prompt.style import ResponseStyle, resolve_response_style
from app.search_planner import SearchPlan
from demo.knowledge_retriever import KnowledgeResult, ProductKnowledge


@dataclass(frozen=True, slots=True)
class PromptBuildResult:
    """ผลลัพธ์จากการสร้าง Prompt."""

    prompt: str
    system_message: str
    has_knowledge: bool
    product_count: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "system_message": self.system_message,
            "has_knowledge": self.has_knowledge,
            "product_count": self.product_count,
            "metadata": dict(self.metadata),
        }


class CommercePromptBuilder:
    """สร้าง Prompt สำหรับ AI Sales Agent ของ Bakery D'Ver."""

    DEFAULT_SYSTEM_MESSAGE = (
        "คุณคือ AI Sales Agent ของร้าน Bakery D'Ver "
        "ตอบลูกค้าเป็นภาษาไทยอย่างสุภาพ กระชับ และตรงคำถาม"
    )

    def build(
    self,
    *,
    customer_message: str,
    platform: str,
    knowledge: KnowledgeResult,
    search_plan: SearchPlan,
    conversation_context: str = "",
    product_context: str = "",
    response_style: (
        str
        | ResponseStyle
        | None
    ) = None,
) -> PromptBuildResult:
        normalized_message = customer_message.strip()
        normalized_platform = platform.strip() or "unknown"
        style = resolve_response_style(
    platform=normalized_platform,
    requested_style=response_style,
)
        style_section = (
    self._build_style_section(
        style
    )
)
        knowledge_section = (
    self._build_knowledge_section(
        knowledge
    )
)
        conversation_section = (
    self._build_conversation_section(
        conversation_context
    )
)
        product_section = (
            self._build_product_section(
                product_context
            )
        )

        if not normalized_message:
            raise ValueError("customer_message ต้องไม่ว่าง")

        prompt = "\n\n".join(
            (
                self._build_role_section(
                    normalized_platform
                ),
                style_section,
                conversation_section,
                product_section,
                knowledge_section,
                self._build_customer_section(
                    normalized_message
                ),
                self._build_rules_section(),
            )
        ).strip()

        return PromptBuildResult(
            prompt=prompt,
            system_message=self.DEFAULT_SYSTEM_MESSAGE,
            has_knowledge=knowledge.found,
            product_count=len(knowledge.products),
            metadata={
                "platform": normalized_platform,
                "searched_models": list(search_plan.extracted_models),
                "matched_keywords": list(knowledge.matched_keywords),
                "knowledge_source": knowledge.source,"response_style": (
    style.to_dict()
),
                
            },
        )

    @staticmethod
    def _build_role_section(platform: str) -> str:
        return (
            "บทบาท\n"
            "คุณคือ AI Sales Agent ของร้าน Bakery D'Ver\n"
            f"แพลตฟอร์ม: {platform}"
        )

    def _build_knowledge_section(
        self,
        knowledge: KnowledgeResult,
    ) -> str:
        if not knowledge.found or not knowledge.products:
            return (
                "ข้อมูลสินค้าที่ตรวจสอบแล้ว\n"
                "ไม่พบข้อมูลสินค้าที่ตรงกับคำถาม"
            )

        blocks = [
            self._format_product(product)
            for product in knowledge.products
        ]

        return (
            "ข้อมูลสินค้าที่ตรวจสอบแล้ว\n"
            + "\n\n".join(blocks)
        )
    @staticmethod
    def _build_conversation_section(
        context: str,
    ) -> str:
        """สร้างส่วนประวัติการสนทนา"""

        if not context.strip():
            return (
                "ประวัติการสนทนา\n"
                "ยังไม่มี"
            )

        return (
            "ประวัติการสนทนา\n"
            f"{context}"
        )
    

    @staticmethod
    def _build_product_section(
        context: str,
    ) -> str:
        """สร้างส่วน Product Slot Memory"""

        if not context.strip():
            return (
                "Product Slots\n"
                "ยังไม่มี"
            )

        return (
            "Product Slots\n"
            f"{context}"
        )
    @staticmethod
    def _format_product(product: ProductKnowledge) -> str:
        lines = [
            f"รหัสสินค้า: {product.model}",
            f"ชื่อสินค้า: {product.name}",
        ]

        optional_fields = (
            ("หมวดสินค้า", product.category),
            ("ขนาดถุงที่ใช้ร่วมกัน", product.compatible_bag),
            ("วัสดุ", product.material),
            ("สี", product.color),
            ("หมายเหตุ", product.notes),
        )

        for label, value in optional_fields:
            cleaned = value.strip()
            if cleaned:
                lines.append(f"{label}: {cleaned}")

        return "\n".join(lines)

    @staticmethod
    def _build_customer_section(customer_message: str) -> str:
        return f"คำถามลูกค้า\n{customer_message}"

    @staticmethod
    def _build_rules_section() -> str:
        rules = (
            "ใช้ข้อมูลสินค้าที่ตรวจสอบแล้วเป็นหลัก",
            "ห้ามแต่งข้อมูลที่ไม่มีอยู่ในระบบ",
            "ห้ามเดาราคา สต็อก โปรโมชั่น หรือค่าจัดส่ง",
            "ถ้าไม่มีข้อมูล ให้แจ้งตามจริงและขอรายละเอียดเพิ่ม",
            "รักษาชื่อร้านว่า Bakery D'Ver ตรงตามนี้",
            "ตอบภาษาไทย สุภาพ กระชับ และตรงคำถาม",
            "ไม่ต้องอธิบายกระบวนการค้นหาหรือระบบภายใน",
        )

        return "กฎการตอบ\n" + "\n".join(
            f"- {rule}" for rule in rules
        )
    
    @staticmethod
    def _build_style_section(
    style,
) -> str:
     """ สร้างส่วนกำหนดรูปแบบคำตอบ """

     return (
        "รูปแบบคำตอบ\n"
        f"{style.instruction}"
      )


def main() -> None:
    from app.search_planner import create_search_plan
    from demo.knowledge_retriever import ProductCatalogRetriever

    message = "รุ่น5040คืออะไร"
    plan = create_search_plan(message)
    knowledge = ProductCatalogRetriever().retrieve(plan)

    result = CommercePromptBuilder().build(
        customer_message=message,
        platform="shopee",
        knowledge=knowledge,
        search_plan=plan,
    )

    print("=" * 60)
    print("Commerce Prompt Builder")
    print("=" * 60)
    print(result.prompt)
    print("=" * 60)


if __name__ == "__main__":
    main()
