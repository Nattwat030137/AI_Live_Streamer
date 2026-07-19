"""
Sales Brain

วิเคราะห์สิ่งที่ลูกค้าน่าจะต้องการ
และแนะนำสินค้าที่ควรเสนอขายเพิ่ม
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.search_executor import SearchExecutionResult


# --------------------------------------------------------
# Cross Sell Rules
# --------------------------------------------------------

CROSS_SELL_RULES = {

    "คัพเค้ก": [
        "กล่องคัพเค้ก",
        "ฝาปิด",
        "สติ๊กเกอร์",
    ],

    "บราวนี่": [
        "กล่องบราวนี่",
        "ถุงซีล",
        "สติ๊กเกอร์",
    ],

    "คุกกี้": [
        "ถุงคุกกี้",
        "ถุงซีล",
        "ริบบิ้น",
    ],

    "เค้ก": [
        "ฐานรองเค้ก",
        "กล่องเค้ก",
        "เทียน",
    ],

}


# --------------------------------------------------------
# Data Model
# --------------------------------------------------------

@dataclass(slots=True)
class SalesSuggestion:

    trigger: str = ""

    keywords: list[str] = field(
        default_factory=list
    )

    reason: str = ""

    @property
    def has_result(self) -> bool:

        return bool(
            self.keywords
        )


# --------------------------------------------------------
# Engine
# --------------------------------------------------------

class SalesBrain:

    def __init__(
        self,
        limit: int = 3,
    ):

        self.limit = limit

    def detect_trigger(
        self,
        message: str,
    ) -> str:

        text = message.lower()

        for trigger in CROSS_SELL_RULES:

            if trigger in text:

                return trigger

        return ""

    def suggest(
        self,
        message: str,
        search_result: SearchExecutionResult,
    ) -> SalesSuggestion:

        trigger = self.detect_trigger(
            message
        )

        if not trigger:

            return SalesSuggestion()

        keywords = list(
            CROSS_SELL_RULES[
                trigger
            ]
        )

        keywords = keywords[
            : self.limit
        ]

        return SalesSuggestion(
            trigger=trigger,
            keywords=keywords,
            reason=(
                "Cross Sell Rule"
            ),
        )