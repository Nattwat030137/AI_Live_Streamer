"""วิเคราะห์อารมณ์และสัญญาณความรู้สึกจากข้อความลูกค้า."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.core.sales_context import (
    EmotionResult,
    EmotionType,
)


class SentimentType(str, Enum):
    """แนวโน้มความรู้สึกโดยรวมของข้อความ."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass(slots=True)
class EmotionAnalysis:
    """ผลวิเคราะห์อารมณ์แบบละเอียด."""

    primary: EmotionResult
    secondary: EmotionType | None = None
    sentiment: SentimentType = SentimentType.NEUTRAL
    intensity: int = 0

    @property
    def has_secondary(self) -> bool:
        """คืน True เมื่อพบอารมณ์รอง."""

        return self.secondary is not None


EMOTION_KEYWORDS: dict[
    EmotionType,
    tuple[str, ...],
] = {
    EmotionType.POSITIVE: (
        "ชอบ",
        "ดีมาก",
        "สวย",
        "ถูกใจ",
        "โอเคเลย",
        "ขอบคุณ",
        "เยี่ยม",
    ),
    EmotionType.INTERESTED: (
        "สนใจ",
        "อยากได้",
        "อยากซื้อ",
        "น่าสนใจ",
        "ขอดู",
        "มีแบบไหน",
        "มีสีอะไร",
    ),
    EmotionType.HESITATING: (
        "ลังเล",
        "ไม่แน่ใจ",
        "ดีไหม",
        "เหมาะไหม",
        "ใช้ได้ไหม",
        "จะดีหรือเปล่า",
    ),
    EmotionType.PRICE_RESISTANCE: (
        "แพง",
        "แพงจัง",
        "แพงมาก",
        "คุ้มไหม",
        "ลดได้ไหม",
        "มีถูกกว่านี้ไหม",
        "งบไม่พอ",
    ),
    EmotionType.NEGATIVE: (
        "ไม่พอใจ",
        "แย่",
        "ไม่โอเค",
        "ผิดหวัง",
        "หงุดหงิด",
        "เสียความรู้สึก",
    ),
    EmotionType.CONFUSED: (
        "งง",
        "ไม่เข้าใจ",
        "สับสน",
        "ต่างกันยังไง",
        "ใช้อันไหน",
        "เลือกไม่ถูก",
    ),
}


EMOTION_BASE_SCORES: dict[
    EmotionType,
    int,
] = {
    EmotionType.POSITIVE: 64,
    EmotionType.INTERESTED: 68,
    EmotionType.HESITATING: 66,
    EmotionType.PRICE_RESISTANCE: 74,
    EmotionType.NEGATIVE: 80,
    EmotionType.CONFUSED: 70,
    EmotionType.NEUTRAL: 0,
}


EMOTION_PRIORITY: dict[
    EmotionType,
    int,
] = {
    EmotionType.NEGATIVE: 6,
    EmotionType.PRICE_RESISTANCE: 5,
    EmotionType.CONFUSED: 4,
    EmotionType.HESITATING: 3,
    EmotionType.INTERESTED: 2,
    EmotionType.POSITIVE: 1,
    EmotionType.NEUTRAL: 0,
}


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


def find_emotion_matches(
    message: str,
    emotion: EmotionType,
) -> list[str]:
    """คืน Keyword ที่ตรงกับอารมณ์ที่ระบุ."""

    normalized_message = (
        message.strip().lower()
    )

    if not normalized_message:
        return []

    keywords = EMOTION_KEYWORDS.get(
        emotion,
        (),
    )

    return [
        keyword
        for keyword in keywords
        if keyword in normalized_message
    ]


def calculate_emotion_score(
    emotion: EmotionType,
    matches: list[str],
    intensity_bonus: int = 0,
) -> int:
    """คำนวณคะแนนอารมณ์จากจำนวน Keyword และความเข้ม."""

    if not matches:
        return 0

    base_score = EMOTION_BASE_SCORES.get(
        emotion,
        0,
    )

    match_bonus = (
        max(
            len(matches) - 1,
            0,
        )
        * 7
    )

    return clamp_score(
        base_score
        + match_bonus
        + max(
            intensity_bonus,
            0,
        )
    )


def detect_text_intensity(
    message: str,
) -> int:
    """ประเมินความเข้มจากเครื่องหมายและรูปแบบข้อความ."""

    cleaned_message = message.strip()

    if not cleaned_message:
        return 0

    score = 0

    exclamation_count = (
        cleaned_message.count("!")
        + cleaned_message.count("！")
    )

    question_count = (
        cleaned_message.count("?")
        + cleaned_message.count("？")
    )

    repeated_marks = min(
        exclamation_count
        + question_count,
        4,
    )

    score += repeated_marks * 4

    if "มากๆ" in cleaned_message:
        score += 8

    if "มาก ๆ" in cleaned_message:
        score += 8

    if "สุดๆ" in cleaned_message:
        score += 10

    if "สุด ๆ" in cleaned_message:
        score += 10

    return clamp_score(
        score
    )


def build_emotion_reason(
    emotion: EmotionType,
    matches: list[str],
) -> str:
    """สร้างเหตุผลอธิบายผลวิเคราะห์อารมณ์."""

    if not matches:
        return (
            "ไม่พบคำที่บ่งบอก"
            "อารมณ์อย่างชัดเจน"
        )

    keyword_text = ", ".join(
        matches
    )

    reason_map = {
        EmotionType.POSITIVE: (
            "ลูกค้ามีสัญญาณเชิงบวก"
        ),
        EmotionType.INTERESTED: (
            "ลูกค้าแสดงความสนใจ"
        ),
        EmotionType.HESITATING: (
            "ลูกค้ายังลังเลหรือไม่แน่ใจ"
        ),
        EmotionType.PRICE_RESISTANCE: (
            "ลูกค้ามีข้อกังวลเรื่องราคา"
        ),
        EmotionType.NEGATIVE: (
            "ลูกค้ามีความรู้สึกเชิงลบ"
        ),
        EmotionType.CONFUSED: (
            "ลูกค้ายังสับสนหรือไม่เข้าใจ"
        ),
    }

    prefix = reason_map.get(
        emotion,
        "ตรวจพบสัญญาณอารมณ์",
    )

    return (
        f"{prefix} จากคำว่า "
        f"{keyword_text}"
    )


def determine_sentiment(
    emotion: EmotionType,
) -> SentimentType:
    """แปลง Emotion เป็น Sentiment โดยรวม."""

    if emotion in {
        EmotionType.POSITIVE,
        EmotionType.INTERESTED,
    }:
        return SentimentType.POSITIVE

    if emotion in {
        EmotionType.NEGATIVE,
        EmotionType.PRICE_RESISTANCE,
        EmotionType.HESITATING,
        EmotionType.CONFUSED,
    }:
        return SentimentType.NEGATIVE

    return SentimentType.NEUTRAL


def analyze_emotion(
    message: str,
) -> EmotionAnalysis:
    """วิเคราะห์อารมณ์หลัก อารมณ์รอง และ Sentiment."""

    cleaned_message = message.strip()

    if not cleaned_message:
        return EmotionAnalysis(
            primary=EmotionResult(
                emotion=EmotionType.NEUTRAL,
                score=0,
                matched_keywords=[],
                reason=(
                    "ไม่มีข้อความสำหรับ"
                    "วิเคราะห์อารมณ์"
                ),
            ),
            sentiment=SentimentType.NEUTRAL,
            intensity=0,
        )

    intensity = detect_text_intensity(
        cleaned_message
    )

    candidates: list[
        tuple[
            EmotionType,
            int,
            list[str],
        ]
    ] = []

    for emotion in EMOTION_KEYWORDS:
        matches = find_emotion_matches(
            cleaned_message,
            emotion,
        )

        score = calculate_emotion_score(
            emotion=emotion,
            matches=matches,
            intensity_bonus=intensity,
        )

        if score <= 0:
            continue

        candidates.append(
            (
                emotion,
                score,
                matches,
            )
        )

    if not candidates:
        return EmotionAnalysis(
            primary=EmotionResult(
                emotion=EmotionType.NEUTRAL,
                score=0,
                matched_keywords=[],
                reason=(
                    "ไม่พบคำที่บ่งบอก"
                    "อารมณ์อย่างชัดเจน"
                ),
            ),
            sentiment=SentimentType.NEUTRAL,
            intensity=intensity,
        )

    ranked_candidates = sorted(
        candidates,
        key=lambda item: (
            item[1],
            EMOTION_PRIORITY[
                item[0]
            ],
        ),
        reverse=True,
    )

    primary_emotion, primary_score, primary_matches = (
        ranked_candidates[0]
    )

    secondary_emotion = (
        ranked_candidates[1][0]
        if len(ranked_candidates) > 1
        else None
    )

    primary_result = EmotionResult(
        emotion=primary_emotion,
        score=primary_score,
        matched_keywords=list(
            primary_matches
        ),
        reason=build_emotion_reason(
            primary_emotion,
            primary_matches,
        ),
    )

    return EmotionAnalysis(
        primary=primary_result,
        secondary=secondary_emotion,
        sentiment=determine_sentiment(
            primary_emotion
        ),
        intensity=intensity,
    )


def apply_emotion_analysis(
    context: object,
    analysis: EmotionAnalysis,
) -> object:
    """
    ใส่ผล Emotion ลง Context ที่มี attribute ชื่อ emotion.

    ใช้ object เพื่อหลีกเลี่ยงการผูก Engine กับ SalesContext
    มากเกินจำเป็น แต่จะตรวจ attribute ก่อนใช้งาน
    """

    if not hasattr(
        context,
        "emotion",
    ):
        raise AttributeError(
            "context ต้องมี attribute ชื่อ emotion"
        )

    setattr(
        context,
        "emotion",
        analysis.primary,
    )

    if hasattr(
        context,
        "update_decision_record",
    ):
        update_method = getattr(
            context,
            "update_decision_record",
        )

        if callable(
            update_method
        ):
            update_method()

    return context


class EmotionEngine:
    """Facade สำหรับวิเคราะห์และใช้ Emotion Result."""

    def analyze(
        self,
        message: str,
    ) -> EmotionAnalysis:
        """วิเคราะห์อารมณ์จากข้อความ."""

        return analyze_emotion(
            message
        )

    def apply(
        self,
        context: object,
        message: str,
    ) -> object:
        """วิเคราะห์และบันทึก Emotion ลง Context."""

        analysis = self.analyze(
            message
        )

        return apply_emotion_analysis(
            context=context,
            analysis=analysis,
        )