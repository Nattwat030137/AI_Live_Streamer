"""Data models กลางสำหรับ Sales Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.customer_intent_score import (
    CustomerIntentScore,
    CustomerStage,
)


class EmotionType(str, Enum):
    """อารมณ์หรือสัญญาณสำคัญจากข้อความลูกค้า."""

    NEUTRAL = "neutral"
    POSITIVE = "positive"
    INTERESTED = "interested"
    HESITATING = "hesitating"
    PRICE_RESISTANCE = "price_resistance"
    NEGATIVE = "negative"
    CONFUSED = "confused"


class CustomerPersonaType(str, Enum):
    """ประเภทลูกค้าที่ระบบรู้จัก."""

    UNKNOWN = "unknown"
    BEGINNER = "beginner"
    HOME_BAKER = "home_baker"
    BAKERY_OWNER = "bakery_owner"
    CAFE_OWNER = "cafe_owner"
    ONLINE_SELLER = "online_seller"
    RESELLER = "reseller"
    FACTORY = "factory"
    GENERAL_CUSTOMER = "general_customer"


class SalesPipelineStage(str, Enum):
    """ขั้นตอนของลูกค้าในกระบวนการขาย."""

    GREETING = "greeting"
    INFORMATION = "information"
    NEED_DISCOVERY = "need_discovery"
    NEED_ANALYSIS = "need_analysis"
    RECOMMENDATION = "recommendation"
    COMPARISON = "comparison"
    OBJECTION = "objection"
    CLOSING = "closing"
    PAYMENT = "payment"
    AFTER_SALE = "after_sale"


class SalesAction(str, Enum):
    """การกระทำหลักที่ AI ควรเลือก."""

    ANSWER = "answer"
    ASK_CLARIFYING_QUESTION = "ask_clarifying_question"
    RECOMMEND = "recommend"
    COMPARE = "compare"
    REDUCE_CONCERN = "reduce_concern"
    GUIDE_ORDER = "guide_order"
    HUMAN_HANDOFF = "human_handoff"
    CLOSE_CONVERSATION = "close_conversation"


@dataclass(slots=True)
class EmotionResult:
    """ผลการวิเคราะห์อารมณ์ของลูกค้า."""

    emotion: EmotionType = EmotionType.NEUTRAL
    score: int = 0
    matched_keywords: list[str] = field(
        default_factory=list
    )
    reason: str = ""

    @property
    def is_negative_signal(self) -> bool:
        """คืน True เมื่อพบอารมณ์ที่ต้องตอบอย่างระมัดระวัง."""

        return self.emotion in {
            EmotionType.PRICE_RESISTANCE,
            EmotionType.NEGATIVE,
            EmotionType.CONFUSED,
        }


@dataclass(slots=True)
class CustomerPersonaResult:
    """ผลการวิเคราะห์ประเภทลูกค้า."""

    persona: CustomerPersonaType = (
        CustomerPersonaType.UNKNOWN
    )
    confidence: int = 0
    matched_keywords: list[str] = field(
        default_factory=list
    )
    reason: str = ""


@dataclass(slots=True)
class SalesStrategy:
    """กลยุทธ์ตอบลูกค้าที่ระบบเลือก."""

    pipeline_stage: SalesPipelineStage = (
        SalesPipelineStage.INFORMATION
    )
    primary_action: SalesAction = SalesAction.ANSWER
    sales_confidence: int = 0
    response_tone: str = "สุภาพและเป็นธรรมชาติ"
    response_goal: str = "ตอบคำถามให้ตรงประเด็น"
    should_recommend: bool = False
    should_upsell: bool = False
    should_cross_sell: bool = False
    should_ask_question: bool = False
    should_handoff: bool = False
    reason: str = ""

    @property
    def can_sell_proactively(self) -> bool:
        """คืน True เมื่อเหมาะกับการเสนอขายเชิงรุก."""

        return (
            self.sales_confidence >= 65
            and not self.should_handoff
        )


@dataclass(slots=True)
class DecisionRecord:
    """บันทึกเหตุผลและผลการตัดสินใจของ AI."""

    original_message: str = ""
    enriched_message: str = ""
    customer_stage: str = ""
    intent_score: int = 0
    emotion: str = ""
    emotion_score: int = 0
    persona: str = ""
    persona_confidence: int = 0
    pipeline_stage: str = ""
    primary_action: str = ""
    sales_confidence: int = 0
    recommendations: list[str] = field(
        default_factory=list
    )
    human_handoff: bool = False
    reasons: list[str] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def add_reason(
        self,
        reason: str,
    ) -> None:
        """เพิ่มเหตุผลโดยไม่เก็บข้อความว่างหรือข้อความซ้ำ."""

        cleaned_reason = reason.strip()

        if not cleaned_reason:
            return

        if cleaned_reason in self.reasons:
            return

        self.reasons.append(
            cleaned_reason
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Decision Record เป็น Dictionary."""

        return {
            "original_message": (
                self.original_message
            ),
            "enriched_message": (
                self.enriched_message
            ),
            "customer_stage": (
                self.customer_stage
            ),
            "intent_score": (
                self.intent_score
            ),
            "emotion": self.emotion,
            "emotion_score": (
                self.emotion_score
            ),
            "persona": self.persona,
            "persona_confidence": (
                self.persona_confidence
            ),
            "pipeline_stage": (
                self.pipeline_stage
            ),
            "primary_action": (
                self.primary_action
            ),
            "sales_confidence": (
                self.sales_confidence
            ),
            "recommendations": list(
                self.recommendations
            ),
            "human_handoff": (
                self.human_handoff
            ),
            "reasons": list(
                self.reasons
            ),
            "metadata": dict(
                self.metadata
            ),
        }


@dataclass(slots=True)
class SalesContext:
    """ข้อมูลกลางที่ทุกโมดูล Sales Intelligence ใช้ร่วมกัน."""

    original_message: str = ""
    enriched_message: str = ""

    customer_intent: CustomerIntentScore = field(
        default_factory=lambda: CustomerIntentScore(
            stage=CustomerStage.INFORMATION,
            score=0,
            matched_keywords=[],
            reason=(
                "ยังไม่ได้วิเคราะห์"
                "ระดับความตั้งใจของลูกค้า"
            ),
        )
    )

    emotion: EmotionResult = field(
        default_factory=EmotionResult
    )

    persona: CustomerPersonaResult = field(
        default_factory=CustomerPersonaResult
    )

    strategy: SalesStrategy = field(
        default_factory=SalesStrategy
    )

    recommendation_keywords: list[str] = field(
        default_factory=list
    )

    decision_record: DecisionRecord = field(
        default_factory=DecisionRecord
    )

    @property
    def should_handoff(self) -> bool:
        """คืน True เมื่อควรส่งต่อแอดมิน."""

        return (
            self.strategy.should_handoff
            or self.decision_record.human_handoff
        )

    @property
    def sales_confidence(self) -> int:
        """คืนคะแนนความเหมาะสมในการเสนอขาย."""

        return self.strategy.sales_confidence

    def update_decision_record(self) -> None:
        """อัปเดต Decision Record จาก Sales Context ปัจจุบัน."""

        record = self.decision_record

        record.original_message = (
            self.original_message
        )

        record.enriched_message = (
            self.enriched_message
        )

        record.customer_stage = (
            self.customer_intent.stage.value
        )

        record.intent_score = (
            self.customer_intent.score
        )

        record.emotion = (
            self.emotion.emotion.value
        )

        record.emotion_score = (
            self.emotion.score
        )

        record.persona = (
            self.persona.persona.value
        )

        record.persona_confidence = (
            self.persona.confidence
        )

        record.pipeline_stage = (
            self.strategy.pipeline_stage.value
        )

        record.primary_action = (
            self.strategy.primary_action.value
        )

        record.sales_confidence = (
            self.strategy.sales_confidence
        )

        record.recommendations = list(
            self.recommendation_keywords
        )

        record.human_handoff = (
            self.should_handoff
        )

        record.add_reason(
            self.customer_intent.reason
        )

        record.add_reason(
            self.emotion.reason
        )

        record.add_reason(
            self.persona.reason
        )

        record.add_reason(
            self.strategy.reason
        )

    def to_dict(self) -> dict[str, Any]:
        """แปลง Sales Context เป็น Dictionary สำหรับ Log หรือ API."""

        self.update_decision_record()

        return {
            "original_message": (
                self.original_message
            ),
            "enriched_message": (
                self.enriched_message
            ),
            "customer_intent": {
                "stage": (
                    self.customer_intent
                    .stage.value
                ),
                "score": (
                    self.customer_intent
                    .score
                ),
                "matched_keywords": list(
                    self.customer_intent
                    .matched_keywords
                ),
                "reason": (
                    self.customer_intent
                    .reason
                ),
            },
            "emotion": {
                "type": (
                    self.emotion.emotion.value
                ),
                "score": self.emotion.score,
                "matched_keywords": list(
                    self.emotion
                    .matched_keywords
                ),
                "reason": self.emotion.reason,
            },
            "persona": {
                "type": (
                    self.persona.persona.value
                ),
                "confidence": (
                    self.persona.confidence
                ),
                "matched_keywords": list(
                    self.persona
                    .matched_keywords
                ),
                "reason": (
                    self.persona.reason
                ),
            },
            "strategy": {
                "pipeline_stage": (
                    self.strategy
                    .pipeline_stage.value
                ),
                "primary_action": (
                    self.strategy
                    .primary_action.value
                ),
                "sales_confidence": (
                    self.strategy
                    .sales_confidence
                ),
                "response_tone": (
                    self.strategy
                    .response_tone
                ),
                "response_goal": (
                    self.strategy
                    .response_goal
                ),
                "should_recommend": (
                    self.strategy
                    .should_recommend
                ),
                "should_upsell": (
                    self.strategy
                    .should_upsell
                ),
                "should_cross_sell": (
                    self.strategy
                    .should_cross_sell
                ),
                "should_ask_question": (
                    self.strategy
                    .should_ask_question
                ),
                "should_handoff": (
                    self.strategy
                    .should_handoff
                ),
                "reason": (
                    self.strategy.reason
                ),
            },
            "recommendation_keywords": list(
                self.recommendation_keywords
            ),
            "decision_record": (
                self.decision_record.to_dict()
            ),
        }