"""วิเคราะห์ระดับความตั้งใจซื้อและสถานะของลูกค้า."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CustomerStage(str, Enum):
    """สถานะของลูกค้าในกระบวนการตัดสินใจซื้อ."""

    BUYING = "buying"
    COMPARING = "comparing"
    INTERESTED = "interested"
    HESITATING = "hesitating"
    INFORMATION = "information"


BUYING_KEYWORDS = (
    "สั่งซื้อ",
    "สั่งเลย",
    "เอา",
    "ซื้อ",
    "ขอ",
    "กดตรงไหน",
    "ชำระเงิน",
    "โอน",
    "เก็บเงินปลายทาง",
    "พร้อมส่งไหม",
    "มีของพร้อมส่งไหม",
)

COMPARING_KEYWORDS = (
    "ต่างกันยังไง",
    "ต่างกันอย่างไร",
    "แบบไหนดีกว่า",
    "อันไหนดีกว่า",
    "เทียบ",
    "เปรียบเทียบ",
    "ระหว่าง",
    "ตัวไหนดี",
    "รุ่นไหนดี",
    "ขนาดไหนดี",
)

HESITATING_KEYWORDS = (
    "แพงไหม",
    "คุ้มไหม",
    "ดีไหม",
    "ใช้ได้ไหม",
    "ไม่แน่ใจ",
    "ลังเล",
    "กลัว",
    "เหมาะไหม",
    "จะดีหรือเปล่า",
    "มีถูกกว่านี้ไหม",
)

INTERESTED_KEYWORDS = (
    "สนใจ",
    "อยากได้",
    "อยากซื้อ",
    "น่าสนใจ",
    "มีสีอะไร",
    "มีแบบไหน",
    "มีรุ่นอะไร",
    "ราคาเท่าไร",
    "ราคาเท่าไหร่",
    "มีของไหม",
    "มีของมั้ย",
)

INFORMATION_KEYWORDS = (
    "คืออะไร",
    "ใช้อย่างไร",
    "ใช้ยังไง",
    "ทำจากอะไร",
    "ขนาดเท่าไร",
    "ขนาดเท่าไหร่",
    "กี่ใบ",
    "กี่ชิ้น",
    "ส่งกี่วัน",
    "จัดส่งอะไร",
    "ส่งที่ไหน",
    "รับเองได้ไหม",
)


@dataclass(slots=True)
class CustomerIntentScore:
    """ผลการวิเคราะห์ความตั้งใจของลูกค้า."""

    stage: CustomerStage
    score: int
    matched_keywords: list[str]
    reason: str

    @property
    def is_high_intent(self) -> bool:
        """คืน True เมื่อลูกค้ามีแนวโน้มซื้อสูง."""

        return (
            self.stage == CustomerStage.BUYING
            and self.score >= 70
        )


def find_matches(
    message: str,
    keywords: tuple[str, ...],
) -> list[str]:
    """คืน Keyword ที่พบในข้อความ."""

    normalized_message = (
        message.strip().lower()
    )

    if not normalized_message:
        return []

    return [
        keyword
        for keyword in keywords
        if keyword in normalized_message
    ]


def calculate_stage_score(
    matches: list[str],
    base_score: int,
    bonus_per_match: int = 8,
) -> int:
    """คำนวณคะแนนโดยจำกัดไว้ไม่เกิน 100."""

    if not matches:
        return 0

    score = (
        base_score
        + max(
            len(matches) - 1,
            0,
        )
        * bonus_per_match
    )

    return min(
        score,
        100,
    )


def build_intent_reason(
    stage: CustomerStage,
    matches: list[str],
) -> str:
    """สร้างเหตุผลประกอบผลวิเคราะห์."""

    if not matches:
        return (
            "ไม่พบคำที่บ่งบอก"
            "ความตั้งใจซื้ออย่างชัดเจน"
        )

    keyword_text = ", ".join(
        matches
    )

    if stage == CustomerStage.BUYING:
        return (
            "ลูกค้าแสดงเจตนาซื้อชัดเจน "
            f"จากคำว่า {keyword_text}"
        )

    if stage == CustomerStage.COMPARING:
        return (
            "ลูกค้ากำลังเปรียบเทียบตัวเลือก "
            f"จากคำว่า {keyword_text}"
        )

    if stage == CustomerStage.HESITATING:
        return (
            "ลูกค้ายังมีข้อกังวลหรือกำลังลังเล "
            f"จากคำว่า {keyword_text}"
        )

    if stage == CustomerStage.INTERESTED:
        return (
            "ลูกค้าแสดงความสนใจสินค้า "
            f"จากคำว่า {keyword_text}"
        )

    return (
        "ลูกค้ากำลังสอบถามข้อมูล "
        f"จากคำว่า {keyword_text}"
    )


def analyze_customer_intent(
    message: str,
) -> CustomerIntentScore:
    """วิเคราะห์สถานะและระดับความตั้งใจซื้อของลูกค้า."""

    cleaned_message = message.strip()

    if not cleaned_message:
        return CustomerIntentScore(
            stage=CustomerStage.INFORMATION,
            score=0,
            matched_keywords=[],
            reason=(
                "ไม่มีข้อความสำหรับวิเคราะห์"
            ),
        )

    buying_matches = find_matches(
        cleaned_message,
        BUYING_KEYWORDS,
    )

    comparing_matches = find_matches(
        cleaned_message,
        COMPARING_KEYWORDS,
    )

    hesitating_matches = find_matches(
        cleaned_message,
        HESITATING_KEYWORDS,
    )

    interested_matches = find_matches(
        cleaned_message,
        INTERESTED_KEYWORDS,
    )

    information_matches = find_matches(
        cleaned_message,
        INFORMATION_KEYWORDS,
    )

    candidates = [
        (
            CustomerStage.BUYING,
            calculate_stage_score(
                buying_matches,
                base_score=78,
            ),
            buying_matches,
        ),
        (
            CustomerStage.COMPARING,
            calculate_stage_score(
                comparing_matches,
                base_score=68,
            ),
            comparing_matches,
        ),
        (
            CustomerStage.HESITATING,
            calculate_stage_score(
                hesitating_matches,
                base_score=60,
            ),
            hesitating_matches,
        ),
        (
            CustomerStage.INTERESTED,
            calculate_stage_score(
                interested_matches,
                base_score=55,
            ),
            interested_matches,
        ),
        (
            CustomerStage.INFORMATION,
            calculate_stage_score(
                information_matches,
                base_score=40,
            ),
            information_matches,
        ),
    ]

    stage_priority = {
        CustomerStage.BUYING: 5,
        CustomerStage.COMPARING: 4,
        CustomerStage.HESITATING: 3,
        CustomerStage.INTERESTED: 2,
        CustomerStage.INFORMATION: 1,
    }

    selected_stage, selected_score, matches = max(
        candidates,
        key=lambda item: (
            item[1],
            stage_priority[item[0]],
        ),
    )

    if selected_score == 0:
        selected_stage = (
            CustomerStage.INFORMATION
        )

    return CustomerIntentScore(
        stage=selected_stage,
        score=selected_score,
        matched_keywords=list(
            matches
        ),
        reason=build_intent_reason(
            selected_stage,
            matches,
        ),
    )


def get_sales_response_strategy(
    intent_score: CustomerIntentScore,
) -> str:
    """คืนแนวทางการตอบที่เหมาะกับสถานะลูกค้า."""

    if intent_score.stage == CustomerStage.BUYING:
        return (
            "ตอบให้ชัดเจน กระชับ "
            "และแนะนำขั้นตอนสั่งซื้อถัดไป"
        )

    if intent_score.stage == CustomerStage.COMPARING:
        return (
            "เปรียบเทียบข้อแตกต่างของตัวเลือก "
            "โดยไม่กล่าวอ้างข้อมูลที่ไม่มี"
        )

    if intent_score.stage == CustomerStage.HESITATING:
        return (
            "ช่วยลดข้อกังวลด้วยข้อมูลจริง "
            "และไม่กดดันให้ลูกค้าซื้อ"
        )

    if intent_score.stage == CustomerStage.INTERESTED:
        return (
            "ตอบรายละเอียดสำคัญ "
            "พร้อมแนะนำสินค้าเกี่ยวข้องอย่างพอดี"
        )

    return (
        "ตอบข้อมูลให้ตรงคำถาม "
        "และขอข้อมูลเพิ่มเติมเมื่อจำเป็น"
    )


class CustomerIntentAnalyzer:
    """Facade สำหรับวิเคราะห์ Intent Score."""

    def analyze(
        self,
        message: str,
    ) -> CustomerIntentScore:
        """วิเคราะห์ข้อความลูกค้า."""

        return analyze_customer_intent(
            message
        )

    def strategy(
        self,
        intent_score: CustomerIntentScore,
    ) -> str:
        """คืนกลยุทธ์การตอบ."""

        return get_sales_response_strategy(
            intent_score
        )