"""เลือกกลยุทธ์การตอบจาก Sales Context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.core.customer_intent_score import CustomerStage
from app.core.sales_context import (
    EmotionType,
    SalesAction,
    SalesContext,
    SalesPipelineStage,
    SalesStrategy,
)


StrategyMatcher = Callable[[SalesContext], bool]
StrategyBuilder = Callable[[SalesContext], SalesStrategy]


@dataclass(frozen=True, slots=True)
class StrategyRule:
    """กฎหนึ่งรายการสำหรับเลือก Sales Strategy."""

    name: str
    priority: int
    matcher: StrategyMatcher
    builder: StrategyBuilder


def clamp_score(
    score: int,
) -> int:
    """จำกัดคะแนนให้อยู่ระหว่าง 0 ถึง 100."""

    return max(
        0,
        min(
            score,
            100,
        ),
    )


def is_buying_customer(
    context: SalesContext,
) -> bool:
    """ตรวจว่าลูกค้ามีแนวโน้มพร้อมซื้อ."""

    return (
        context.customer_intent.stage
        == CustomerStage.BUYING
    )


def is_comparing_customer(
    context: SalesContext,
) -> bool:
    """ตรวจว่าลูกค้ากำลังเปรียบเทียบ."""

    return (
        context.customer_intent.stage
        == CustomerStage.COMPARING
    )


def is_hesitating_customer(
    context: SalesContext,
) -> bool:
    """ตรวจว่าลูกค้ากำลังลังเลหรือมีข้อกังวล."""

    return (
        context.customer_intent.stage
        == CustomerStage.HESITATING
        or context.emotion.emotion
        in {
            EmotionType.HESITATING,
            EmotionType.PRICE_RESISTANCE,
            EmotionType.CONFUSED,
        }
    )


def is_interested_customer(
    context: SalesContext,
) -> bool:
    """ตรวจว่าลูกค้าแสดงความสนใจ."""

    return (
        context.customer_intent.stage
        == CustomerStage.INTERESTED
    )


def should_handoff_customer(
    context: SalesContext,
) -> bool:
    """ตรวจสัญญาณที่ควรส่งต่อแอดมิน."""

    handoff_keywords = (
        "ราคาพิเศษ",
        "ส่วนลดพิเศษ",
        "เคลม",
        "คืนเงิน",
        "ร้องเรียน",
        "สินค้าเสีย",
        "ของชำรุด",
        "รับประกัน",
        "ใบกำกับภาษี",
        "สั่งจำนวนมาก",
        "ราคาส่ง",
    )

    message = (
        context.enriched_message
        or context.original_message
    ).lower()

    return any(
        keyword in message
        for keyword in handoff_keywords
    )


def build_handoff_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """สร้างกลยุทธ์ส่งต่อแอดมิน."""

    del context

    return SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.OBJECTION
        ),
        primary_action=(
            SalesAction.HUMAN_HANDOFF
        ),
        sales_confidence=20,
        response_tone=(
            "สุภาพ ชัดเจน และไม่ให้ข้อมูลเกินขอบเขต"
        ),
        response_goal=(
            "ส่งต่อเรื่องที่ต้องใช้การตรวจสอบจากแอดมิน"
        ),
        should_recommend=False,
        should_upsell=False,
        should_cross_sell=False,
        should_ask_question=False,
        should_handoff=True,
        reason=(
            "ข้อความเกี่ยวข้องกับเงื่อนไขพิเศษ "
            "ข้อร้องเรียน หรือข้อมูลที่ต้องให้แอดมินตรวจสอบ"
        ),
    )


def build_buying_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """สร้างกลยุทธ์สำหรับลูกค้าที่พร้อมซื้อ."""

    score = clamp_score(
        max(
            82,
            context.customer_intent.score,
        )
    )

    return SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.CLOSING
        ),
        primary_action=(
            SalesAction.GUIDE_ORDER
        ),
        sales_confidence=score,
        response_tone=(
            "กระชับ มั่นใจ และสุภาพ"
        ),
        response_goal=(
            "ช่วยลูกค้าไปยังขั้นตอนสั่งซื้อถัดไป"
        ),
        should_recommend=False,
        should_upsell=False,
        should_cross_sell=False,
        should_ask_question=False,
        should_handoff=False,
        reason=(
            "ลูกค้าแสดงเจตนาซื้อชัดเจน "
            "จึงควรช่วยปิดการขายก่อนเสนอสินค้าเพิ่มเติม"
        ),
    )


def build_comparing_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """สร้างกลยุทธ์สำหรับลูกค้าที่กำลังเปรียบเทียบ."""

    score = clamp_score(
        max(
            62,
            context.customer_intent.score,
        )
    )

    return SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.COMPARISON
        ),
        primary_action=(
            SalesAction.COMPARE
        ),
        sales_confidence=score,
        response_tone=(
            "เป็นกลาง ชัดเจน และช่วยตัดสินใจ"
        ),
        response_goal=(
            "เปรียบเทียบความแตกต่างจากข้อมูลจริง"
        ),
        should_recommend=True,
        should_upsell=False,
        should_cross_sell=False,
        should_ask_question=False,
        should_handoff=False,
        reason=(
            "ลูกค้ากำลังเปรียบเทียบตัวเลือก "
            "จึงควรอธิบายความแตกต่างอย่างเป็นกลาง"
        ),
    )


def build_hesitating_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """สร้างกลยุทธ์สำหรับลูกค้าที่ลังเล."""

    confidence = clamp_score(
        max(
            35,
            min(
                context.customer_intent.score,
                58,
            ),
        )
    )

    return SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.OBJECTION
        ),
        primary_action=(
            SalesAction.REDUCE_CONCERN
        ),
        sales_confidence=confidence,
        response_tone=(
            "อ่อนโยน ให้ข้อมูล และไม่กดดัน"
        ),
        response_goal=(
            "ช่วยลดข้อกังวลด้วยข้อมูลที่ตรวจสอบได้"
        ),
        should_recommend=False,
        should_upsell=False,
        should_cross_sell=False,
        should_ask_question=True,
        should_handoff=False,
        reason=(
            "ลูกค้ามีสัญญาณลังเลหรือกังวล "
            "จึงควรตอบข้อกังวลก่อนการเสนอขาย"
        ),
    )


def build_interested_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """สร้างกลยุทธ์สำหรับลูกค้าที่สนใจสินค้า."""

    score = clamp_score(
        max(
            55,
            context.customer_intent.score,
        )
    )

    should_sell = score >= 65

    return SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.RECOMMENDATION
        ),
        primary_action=(
            SalesAction.RECOMMEND
        ),
        sales_confidence=score,
        response_tone=(
            "เป็นกันเองและช่วยตัดสินใจ"
        ),
        response_goal=(
            "ตอบข้อมูลหลักและแนะนำสิ่งที่เกี่ยวข้องอย่างพอดี"
        ),
        should_recommend=True,
        should_upsell=False,
        should_cross_sell=should_sell,
        should_ask_question=False,
        should_handoff=False,
        reason=(
            "ลูกค้าแสดงความสนใจสินค้า "
            "จึงสามารถแนะนำข้อมูลและสินค้าที่เกี่ยวข้องได้"
        ),
    )


def build_information_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """สร้างกลยุทธ์เริ่มต้นสำหรับคำถามข้อมูลทั่วไป."""

    score = clamp_score(
        min(
            context.customer_intent.score,
            40,
        )
    )

    return SalesStrategy(
        pipeline_stage=(
            SalesPipelineStage.INFORMATION
        ),
        primary_action=(
            SalesAction.ANSWER
        ),
        sales_confidence=score,
        response_tone=(
            "สุภาพ ชัดเจน และตรงคำถาม"
        ),
        response_goal=(
            "ตอบข้อมูลให้ครบก่อนเสนอขาย"
        ),
        should_recommend=False,
        should_upsell=False,
        should_cross_sell=False,
        should_ask_question=False,
        should_handoff=False,
        reason=(
            "ลูกค้ากำลังสอบถามข้อมูลทั่วไป "
            "จึงควรตอบตรงประเด็นก่อน"
        ),
    )


STRATEGY_RULES: tuple[StrategyRule, ...] = (
    StrategyRule(
        name="human_handoff",
        priority=100,
        matcher=should_handoff_customer,
        builder=build_handoff_strategy,
    ),
    StrategyRule(
        name="buying",
        priority=90,
        matcher=is_buying_customer,
        builder=build_buying_strategy,
    ),
    StrategyRule(
        name="comparing",
        priority=80,
        matcher=is_comparing_customer,
        builder=build_comparing_strategy,
    ),
    StrategyRule(
        name="hesitating",
        priority=70,
        matcher=is_hesitating_customer,
        builder=build_hesitating_strategy,
    ),
    StrategyRule(
        name="interested",
        priority=60,
        matcher=is_interested_customer,
        builder=build_interested_strategy,
    ),
)


def select_strategy_rule(
    context: SalesContext,
) -> StrategyRule | None:
    """เลือกกฎที่ตรงและมี Priority สูงที่สุด."""

    matching_rules = [
        rule
        for rule in STRATEGY_RULES
        if rule.matcher(
            context
        )
    ]

    if not matching_rules:
        return None

    return max(
        matching_rules,
        key=lambda rule: rule.priority,
    )


def choose_sales_strategy(
    context: SalesContext,
) -> SalesStrategy:
    """เลือกกลยุทธ์หลักจาก Sales Context."""

    selected_rule = select_strategy_rule(
        context
    )

    if selected_rule is None:
        return build_information_strategy(
            context
        )

    return selected_rule.builder(
        context
    )


def apply_sales_strategy(
    context: SalesContext,
) -> SalesContext:
    """เลือก Strategy อัปเดต Context และ Decision Record."""

    context.strategy = (
        choose_sales_strategy(
            context
        )
    )

    context.update_decision_record()

    return context


class StrategyEngine:
    """Facade สำหรับวิเคราะห์และใช้ Sales Strategy."""

    def choose(
        self,
        context: SalesContext,
    ) -> SalesStrategy:
        """เลือก Strategy โดยไม่แก้ Context."""

        return choose_sales_strategy(
            context
        )

    def apply(
        self,
        context: SalesContext,
    ) -> SalesContext:
        """เลือก Strategy และบันทึกลง Context."""

        return apply_sales_strategy(
            context
        )