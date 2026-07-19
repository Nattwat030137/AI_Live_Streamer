"""ข้อมูลตัวอย่างสำหรับ Bakery D'Ver Demo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DemoScenario:
    """Scenario ตัวอย่างหนึ่งรายการ."""

    scenario_id: str
    title: str
    customer_message: str
    platform: str = "shopee"
    expected_rule: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """ตรวจข้อมูลที่จำเป็น."""

        if not self.scenario_id.strip():
            raise ValueError(
                "DemoScenario.scenario_id ต้องไม่ว่าง"
            )

        if not self.title.strip():
            raise ValueError(
                "DemoScenario.title ต้องไม่ว่าง"
            )

        if not self.customer_message.strip():
            raise ValueError(
                "DemoScenario.customer_message ต้องไม่ว่าง"
            )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Scenario เป็น Dictionary."""

        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "customer_message": (
                self.customer_message
            ),
            "platform": self.platform,
            "expected_rule": (
                self.expected_rule
            ),
            "description": self.description,
        }


DEMO_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario(
        scenario_id="product-5040",
        title="สอบถามสินค้ารุ่น 5040",
        customer_message=(
            "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
        ),
        platform="shopee",
        expected_rule="PRODUCT_MODEL_5040",
        description=(
            "ทดสอบคำถามข้อมูลสินค้า"
        ),
    ),
    DemoScenario(
        scenario_id="price-request",
        title="สอบถามราคา",
        customer_message=(
            "รุ่นนี้ราคาเท่าไหร่ครับ"
        ),
        platform="shopee",
        expected_rule="PRICE_REQUEST",
        description=(
            "ต้องไม่เดาราคาและควรส่งต่อแอดมิน"
        ),
    ),
    DemoScenario(
        scenario_id="stock-request",
        title="สอบถามสต็อก",
        customer_message=(
            "มีของพร้อมส่งไหมครับ"
        ),
        platform="shopee",
        expected_rule="STOCK_REQUEST",
        description=(
            "ต้องไม่เดาสต็อกล่าสุด"
        ),
    ),
    DemoScenario(
        scenario_id="shipping-request",
        title="สอบถามค่าจัดส่ง",
        customer_message=(
            "มีส่งฟรีไหม"
        ),
        platform="shopee",
        expected_rule="SHIPPING_REQUEST",
        description=(
            "ตอบตามเงื่อนไขแพลตฟอร์ม"
        ),
    ),
    DemoScenario(
        scenario_id="thank-you",
        title="ลูกค้าขอบคุณ",
        customer_message="ขอบคุณครับ",
        platform="line",
        expected_rule="THANK_YOU",
        description=(
            "ตอบรับอย่างสุภาพและเป็นธรรมชาติ"
        ),
    ),
    DemoScenario(
        scenario_id="general-question",
        title="คำถามทั่วไป",
        customer_message=(
            "ช่วยแนะนำสินค้าสำหรับร้านเบเกอรี่หน่อย"
        ),
        platform="website",
        expected_rule="DEFAULT",
        description=(
            "Fallback สำหรับข้อความที่ยังไม่มีกฎเฉพาะ"
        ),
    ),
)


def get_scenario(
    scenario_id: str,
) -> DemoScenario | None:
    """ค้น Scenario จาก ID."""

    normalized_id = (
        scenario_id.strip().lower()
    )

    for scenario in DEMO_SCENARIOS:
        if (
            scenario.scenario_id.lower()
            == normalized_id
        ):
            return scenario

    return None


def require_scenario(
    scenario_id: str,
) -> DemoScenario:
    """ค้น Scenario และเกิด KeyError เมื่อไม่พบ."""

    scenario = get_scenario(
        scenario_id
    )

    if scenario is None:
        raise KeyError(
            f"ไม่พบ Demo Scenario: {scenario_id}"
        )

    return scenario


def list_scenario_ids() -> tuple[str, ...]:
    """คืน Scenario ID ทั้งหมด."""

    return tuple(
        scenario.scenario_id
        for scenario in DEMO_SCENARIOS
    )