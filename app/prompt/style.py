"""Response style controls สำหรับ AI Commerce OS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ResponseStyle(StrEnum):
    """รูปแบบความยาวและรายละเอียดของคำตอบ."""

    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"


@dataclass(frozen=True, slots=True)
class ResponseStyleConfig:
    """ค่าควบคุมการตอบสำหรับแต่ละรูปแบบ."""

    style: ResponseStyle
    instruction: str
    max_sentences: int | None
    prefer_bullets: bool

    def to_dict(self) -> dict[str, object]:
        """แปลง Config เป็น Dictionary."""

        return {
            "style": self.style.value,
            "instruction": self.instruction,
            "max_sentences": self.max_sentences,
            "prefer_bullets": self.prefer_bullets,
        }


_STYLE_CONFIGS: dict[
    ResponseStyle,
    ResponseStyleConfig,
] = {
    ResponseStyle.BRIEF: ResponseStyleConfig(
        style=ResponseStyle.BRIEF,
        instruction=(
            "ตอบสั้นมาก ไม่เกิน 2 ประโยค "
            "เน้นคำตอบตรงคำถาม และไม่ใส่รายละเอียดเกินจำเป็น"
        ),
        max_sentences=2,
        prefer_bullets=False,
    ),
    ResponseStyle.STANDARD: ResponseStyleConfig(
        style=ResponseStyle.STANDARD,
        instruction=(
            "ตอบกระชับ อ่านง่าย ถ้ามีหลายประเด็น "
            "ให้ใช้หัวข้อย่อยสั้น ๆ"
        ),
        max_sentences=6,
        prefer_bullets=True,
    ),
    ResponseStyle.DETAILED: ResponseStyleConfig(
        style=ResponseStyle.DETAILED,
        instruction=(
            "ตอบอย่างละเอียด โดยยังคงสุภาพและชัดเจน "
            "สามารถใช้หัวข้อย่อยเพื่ออธิบายข้อมูลครบถ้วน"
        ),
        max_sentences=None,
        prefer_bullets=True,
    ),
}


_PLATFORM_DEFAULTS: dict[str, ResponseStyle] = {
    "shopee": ResponseStyle.BRIEF,
    "tiktok": ResponseStyle.BRIEF,
    "line": ResponseStyle.STANDARD,
    "line_oa": ResponseStyle.STANDARD,
    "facebook": ResponseStyle.STANDARD,
    "web": ResponseStyle.STANDARD,
}


def parse_response_style(
    value: str | ResponseStyle | None,
) -> ResponseStyle | None:
    """แปลงค่าเป็น ResponseStyle."""

    if value is None:
        return None

    if isinstance(value, ResponseStyle):
        return value

    normalized = value.strip().lower()

    if not normalized:
        return None

    aliases = {
        "short": ResponseStyle.BRIEF,
        "compact": ResponseStyle.BRIEF,
        "normal": ResponseStyle.STANDARD,
        "default": ResponseStyle.STANDARD,
        "long": ResponseStyle.DETAILED,
        "full": ResponseStyle.DETAILED,
    }

    if normalized in aliases:
        return aliases[normalized]

    try:
        return ResponseStyle(normalized)
    except ValueError as error:
        raise ValueError(
            f"ไม่รองรับ response style: {value!r}"
        ) from error


def resolve_response_style(
    *,
    platform: str,
    requested_style: str | ResponseStyle | None = None,
) -> ResponseStyleConfig:
    """เลือก Response Style จากค่าที่ขอหรือค่าเริ่มต้นแพลตฟอร์ม."""

    parsed_style = parse_response_style(
        requested_style
    )

    if parsed_style is None:
        normalized_platform = (
            platform.strip().lower()
        )

        parsed_style = _PLATFORM_DEFAULTS.get(
            normalized_platform,
            ResponseStyle.STANDARD,
        )

    return _STYLE_CONFIGS[
        parsed_style
    ]


def supported_response_styles() -> tuple[str, ...]:
    """คืนรายชื่อ Style ที่รองรับ."""

    return tuple(
        style.value
        for style in ResponseStyle
    )
