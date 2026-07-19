"""Mock LLM Provider สำหรับ Bakery D'Ver Demo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from demo.knowledge_retriever import (
    KnowledgeResult,
    ProductKnowledge,
)


@dataclass(frozen=True, slots=True)
class MockLLMResponse:
    """ผลลัพธ์จาก Mock LLM."""

    text: str
    response_type: str
    matched_rule: str
    model: str = "mock-bakery-v3"

    def to_dict(self) -> dict[str, Any]:
        """แปลงผลลัพธ์เป็น Dictionary."""

        return {
            "text": self.text,
            "response_type": self.response_type,
            "matched_rule": self.matched_rule,
            "model": self.model,
        }


class MockLLMProvider:
    """
    Mock LLM ที่ตอบจาก Rule และ Product Knowledge.

    ไม่มีการเรียก API, Network หรือ Database ภายนอก
    จึงเหมาะสำหรับ Demo และ Integration Test
    """

    MODEL_NAME = "mock-bakery-v2"

    def generate(
    self,
    prompt: str,
    *,
    customer_message: str = "",
    knowledge: KnowledgeResult | None = None,
    product_attribute: str | None = None,
) -> MockLLMResponse:
        """
        สร้างคำตอบจากข้อความลูกค้าและ Knowledge.

        Rule Classification ต้องตรวจเฉพาะ customer_message
        ห้ามนำ prompt ไปตรวจ Intent หรือ Keyword
        """

        customer_text = (
            customer_message
            .strip()
            .lower()
        )

        if not customer_text:
            return self._answer_empty_message()

        # คำทักทายทั่วไป
        if self._contains_any(
            customer_text,
            (
                "สวัสดี",
                "หวัดดี",
                "hello",
                "hi",
            ),
        ):
         return self._answer_greeting()

        # Intent เฉพาะต้องถูกตรวจ ก่อน Product Knowledge
        if self._contains_any(
            customer_text,
            (
                "ราคาเท่าไหร่",
                "ราคาเท่าไร",
                "กี่บาท",
                "ขอราคา",
                "ราคา",
            ),
        ):
            return self._answer_price()

        if self._contains_any(
            customer_text,
            (
                "พร้อมส่งไหม",
                "พร้อมส่งมั้ย",
                "มีของไหม",
                "มีของหรือเปล่า",
                "มีสต็อกไหม",
                "ของพร้อมส่ง",
                "สต็อก",
            ),
        ):
            return self._answer_stock()

        if self._contains_any(
            customer_text,
            (
                "ส่งฟรีไหม",
                "ส่งฟรีมั้ย",
                "มีส่งฟรี",
                "ค่าส่ง",
                "ค่าจัดส่ง",
            ),
        ):
            return self._answer_shipping()

        if self._contains_any(
            customer_text,
            (
                "ขอบคุณ",
                "โอเคครับ",
                "โอเคค่ะ",
                "รับทราบ",
            ),
        ):
            return self._answer_thank_you()

        # ใช้ข้อมูลสินค้าเมื่อไม่มี Intent เฉพาะด้านบน
        knowledge_response = (
            self._answer_from_knowledge(
                customer_text=customer_text,
                knowledge=knowledge,
                product_attribute=product_attribute,
            )
        )

        if knowledge_response is not None:
            return knowledge_response

        return self._answer_default()

    def generate_text(
        self,
        prompt: str,
        *,
        customer_message: str = "",
        knowledge: KnowledgeResult | None = None,
        product_attribute: str | None = None,
    ) -> str:
        """สร้างและคืนเฉพาะข้อความตอบกลับ."""

        return self.generate(
    prompt=prompt,
    customer_message=customer_message,
    knowledge=knowledge,
    product_attribute=product_attribute,
).text

    def _answer_from_knowledge(
        self,
        *,
        customer_text: str,
        knowledge: KnowledgeResult | None,
        product_attribute: str | None = None,
    ) -> MockLLMResponse | None:
        """สร้างคำตอบจาก Product Catalog เมื่อพบสินค้า."""

        if knowledge is None or not knowledge.found:
            return None

        product = knowledge.primary_product

        if product is None:
            return None

        normalized_attribute = (
            product_attribute or "general"
        ).strip().lower()

        if normalized_attribute == "name":
            if product.name:
                return self._build_response(
                    text=f"{product.name} ค่ะ",
                    response_type="knowledge_product_name",
                    matched_rule="PRODUCT_CATALOG",
                )

            return self._build_response(
                text=(
                    f"ขณะนี้ยังไม่มีข้อมูลชื่อสินค้าของ "
                    f"รุ่น {product.model} ในระบบค่ะ"
                ),
                response_type="knowledge_product_name_missing",
                matched_rule="PRODUCT_CATALOG",
            )

        if normalized_attribute == "color":
            if product.color:
                return self._build_response(
                    text=(
                        f"{product.name} "
                        f"มีสี {product.color} ค่ะ"
                    ),
                    response_type="knowledge_product_color",
                    matched_rule="PRODUCT_CATALOG",
                )

            return self._build_response(
                text=(
                    f"ขณะนี้ยังไม่มีข้อมูลสีของ "
                    f"{product.name} ในระบบค่ะ"
                ),
                response_type="knowledge_product_color_missing",
                matched_rule="PRODUCT_CATALOG",
            )

        if normalized_attribute == "material":
            if product.material:
                return self._build_response(
                    text=(
                        f"{product.name} "
                        f"ผลิตจากวัสดุ {product.material} ค่ะ"
                    ),
                    response_type="knowledge_product_material",
                    matched_rule="PRODUCT_CATALOG",
                )

            return self._build_response(
                text=(
                    f"ขณะนี้ยังไม่มีข้อมูลวัสดุของ "
                    f"{product.name} ในระบบค่ะ"
                ),
                response_type="knowledge_product_material_missing",
                matched_rule="PRODUCT_CATALOG",
            )

        if normalized_attribute == "bag":
            if product.compatible_bag:
                return self._build_response(
                    text=(
                        f"{product.name} "
                        f"ใช้ถุงขนาด {product.compatible_bag} ค่ะ"
                    ),
                    response_type="knowledge_compatible_bag",
                    matched_rule="PRODUCT_CATALOG_COMPATIBLE_BAG",
                )

            return self._build_response(
                text=(
                    f"ขณะนี้ยังไม่มีข้อมูลขนาดถุงที่ใช้กับ "
                    f"{product.name} ในระบบค่ะ"
                ),
                response_type="knowledge_compatible_bag_missing",
                matched_rule="PRODUCT_CATALOG_COMPATIBLE_BAG",
            )
                   
        if normalized_attribute == "category":
            if product.category:
                return self._build_response(
                    text=(
                        f"{product.name} "
                        f"อยู่ในหมวดสินค้า {product.category} ค่ะ"
                    ),
                    response_type="knowledge_product_category",
                    matched_rule="PRODUCT_CATALOG",
                )

            return self._build_response(
                text=(
                    f"ขณะนี้ยังไม่มีข้อมูลหมวดสินค้าของ "
                    f"{product.name} ในระบบค่ะ"
                ),
                response_type="knowledge_product_category_missing",
                matched_rule="PRODUCT_CATALOG",
            )

        if normalized_attribute == "note":
            if product.notes:
                return self._build_response(
                    text=product.notes,
                    response_type="knowledge_product_note",
                    matched_rule="PRODUCT_CATALOG",
                )

            return self._build_response(
                text=(
                    f"ขณะนี้ยังไม่มีหมายเหตุของ "
                    f"{product.name} ในระบบค่ะ"
                ),
                response_type="knowledge_product_note_missing",
                matched_rule="PRODUCT_CATALOG",
            )

            
        return self._build_response(
            text=(
                f"{product.model} คือ "
                f"{product.name} ค่ะ"
            ),
            response_type="knowledge_product_information",
            matched_rule="PRODUCT_CATALOG",
        )
    
    def _answer_stock(
        self,
    ) -> MockLLMResponse:
        """ตอบคำถามสต็อกโดยไม่เดาข้อมูล."""

        return self._build_response(
            text=(
                "ขออนุญาตให้แอดมินตรวจสอบ"
                "สต็อกล่าสุดให้นะคะ "
                "เพื่อยืนยันจำนวนสินค้าที่พร้อมส่งค่ะ"
            ),
            response_type="stock_handoff",
            matched_rule="STOCK_REQUEST",
        )

    def _answer_shipping(
        self,
    ) -> MockLLMResponse:
        """ตอบคำถามเรื่องค่าจัดส่ง."""

        return self._build_response(
            text=(
                "ค่าจัดส่งและสิทธิ์ส่งฟรีขึ้นอยู่กับ"
                "เงื่อนไขของคำสั่งซื้อและแพลตฟอร์มค่ะ "
                "กรุณาตรวจสอบรายละเอียดที่หน้าคำสั่งซื้อ"
                "ก่อนชำระเงินนะคะ"
            ),
            response_type="shipping_information",
            matched_rule="SHIPPING_REQUEST",
        )

    def _answer_thank_you(
        self,
    ) -> MockLLMResponse:
        """ตอบรับคำขอบคุณ."""

        return self._build_response(
            text=(
                "ยินดีมากค่ะ หากต้องการสอบถาม"
                "สินค้าเพิ่มเติม แจ้งได้เลยนะคะ"
            ),
            response_type=(
                "customer_acknowledgement"
            ),
            matched_rule="THANK_YOU",
        )

    def _answer_default(
        self,
    ) -> MockLLMResponse:
        """ตอบเมื่อยังไม่พบ Rule หรือ Knowledge."""

        return self._build_response(
            text=(
                "ยินดีช่วยตรวจสอบให้ค่ะ "
                "รบกวนแจ้งชื่อสินค้า รุ่น ขนาด "
                "หรือรายละเอียดที่ต้องการเพิ่มเติม"
                "ได้เลยนะคะ"
            ),
            response_type="general_assistance",
            matched_rule="DEFAULT",
        )

    def _build_response(
        self,
        *,
        text: str,
        response_type: str,
        matched_rule: str,
    ) -> MockLLMResponse:
        """สร้าง MockLLMResponse มาตรฐาน."""

        return MockLLMResponse(
            text=text.strip(),
            response_type=response_type,
            matched_rule=matched_rule,
            model=self.MODEL_NAME,
        )

    @staticmethod
    def _contains_any(
        text: str,
        keywords: tuple[str, ...],
    ) -> bool:
        """ตรวจว่าข้อความมี Keyword อย่างน้อยหนึ่งรายการ."""

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _format_notes(
        notes: str,
    ) -> str:
        """จัดรูปแบบหมายเหตุของสินค้า."""

        cleaned_notes = notes.strip()

        if not cleaned_notes:
            return ""
            

        return (
            f" หมายเหตุ: {cleaned_notes}"
        )