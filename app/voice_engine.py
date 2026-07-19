"""ระบบสร้างและเล่นเสียงภาษาไทยด้วย OpenAI Speech API."""

import re
from pathlib import Path

import pygame
from openai import OpenAI

from app.prompt_loader import load_prompt
from config.settings import OPENAI_API_KEY, PROJECT_ROOT
from core.logger import logger


# =========================================================
# ตำแหน่งไฟล์เสียง
# =========================================================

AUDIO_DIR = PROJECT_ROOT / "audio"
VOICE_FILE = AUDIO_DIR / "ai_voice.mp3"


# =========================================================
# การตั้งค่าเสียง
# =========================================================

TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "marin"
TTS_SPEED = 1.10

VOICE_INSTRUCTIONS = load_prompt(
    "voice_prompt.txt"
)


# =========================================================
# คำอ่านตัวเลข
# =========================================================

THAI_DIGITS = {
    "0": "ศูนย์",
    "1": "หนึ่ง",
    "2": "สอง",
    "3": "สาม",
    "4": "สี่",
    "5": "ห้า",
    "6": "หก",
    "7": "เจ็ด",
    "8": "แปด",
    "9": "เก้า",
}


# =========================================================
# คำภาษาอังกฤษที่ต้องแปลงเฉพาะเสียง
# =========================================================

VOICE_WORD_REPLACEMENTS = {
    "Transparent": "สีใส",
    "Natural": "สีธรรมชาติ",
    "Silver": "สีเงิน",
    "Orange": "สีส้ม",
    "Purple": "สีม่วง",
    "Yellow": "สีเหลือง",
    "Coffee": "สีกาแฟ",
    "Brown": "สีน้ำตาล",
    "White": "สีขาว",
    "Black": "สีดำ",
    "Green": "สีเขียว",
    "Cream": "สีครีม",
    "Clear": "สีใส",
    "Kraft": "คราฟท์",
    "Pink": "สีชมพู",
    "Blue": "สีน้ำเงิน",
    "Gold": "สีทอง",
    "Gray": "สีเทา",
    "Grey": "สีเทา",
    "Red": "สีแดง",
}


def replace_english_words(text: str) -> str:
    """แปลงคำอังกฤษเป็นภาษาไทยสำหรับเสียง."""

    prepared_text = text

    for english_word, thai_word in VOICE_WORD_REPLACEMENTS.items():
        pattern = re.compile(
            rf"(?<![A-Za-z])"
            rf"{re.escape(english_word)}"
            rf"(?![A-Za-z])",
            flags=re.IGNORECASE,
        )

        prepared_text = pattern.sub(
            thai_word,
            prepared_text,
        )

    return prepared_text


def digits_to_spoken_code(number_text: str) -> str:
    """เปลี่ยนเลขรหัสให้อ่านทีละหลัก."""

    spoken_digits: list[str] = []

    for character in number_text:
        if character in THAI_DIGITS:
            spoken_digits.append(
                THAI_DIGITS[character]
            )

    return " ".join(spoken_digits)


def replace_labeled_code_number(
    match: re.Match[str],
) -> str:
    """แปลงตัวเลขหลังคำว่า รุ่น รหัส SKU หรือเบอร์."""

    label = match.group("label")
    number = match.group("number")

    spoken_number = digits_to_spoken_code(
        number
    )

    return f"{label} {spoken_number}"


def replace_product_model_number(
    match: re.Match[str],
) -> str:
    """แปลงเลขรุ่นที่ติดอยู่หลังชื่อสินค้า."""

    product_word = match.group("product")
    number = match.group("number")

    spoken_number = digits_to_spoken_code(
        number
    )

    return (
        f"{product_word} รุ่น "
        f"{spoken_number}"
    )


def improve_thai_spacing(text: str) -> str:
    """ปรับข้อความหลังแปลงคำให้เสียงอ่านลื่นขึ้น."""

    prepared_text = text

    prepared_text = re.sub(
        r"(สีขาว|สีน้ำตาล|สีดำ|สีครีม)"
        r"\s*ไม่เคลือบ",
        r"\1 แบบไม่เคลือบ",
        prepared_text,
    )

    prepared_text = re.sub(
        r"(สีขาว|สีน้ำตาล|สีดำ|สีครีม)"
        r"\s*เคลือบ",
        r"\1 แบบเคลือบ",
        prepared_text,
    )

    prepared_text = re.sub(
        r"สี\s+(สีขาว|สีน้ำตาล|สีดำ|สีแดง|"
        r"สีน้ำเงิน|สีชมพู|สีเขียว|สีเหลือง|"
        r"สีม่วง|สีส้ม|สีเทา|สีทอง|สีเงิน|"
        r"สีครีม|สีใส|สีกาแฟ)",
        r"\1",
        prepared_text,
    )

    prepared_text = re.sub(
        r"\s+และ\s+",
        "และ",
        prepared_text,
    )

    return prepared_text


def prepare_text(text: str) -> str:
    """เตรียมข้อความก่อนส่งให้ OpenAI Speech API."""

    prepared_text = text.strip()

    prepared_text = re.sub(
        r"[*#_~`]",
        "",
        prepared_text,
    )

    prepared_text = replace_english_words(
        prepared_text
    )

    labeled_code_pattern = re.compile(
        r"(?P<label>"
        r"รุ่น|"
        r"โมเดล|"
        r"รหัสสินค้า|"
        r"รหัส|"
        r"SKU|"
        r"เอสเคยู|"
        r"เบอร์"
        r")"
        r"\s*"
        r"(?P<number>\d{2,})",
        flags=re.IGNORECASE,
    )

    prepared_text = labeled_code_pattern.sub(
        replace_labeled_code_number,
        prepared_text,
    )

    product_model_pattern = re.compile(
        r"(?P<product>"
        r"ถ้วยคัพเค้ก|"
        r"คัพเค้ก|"
        r"พิมพ์|"
        r"ถาด|"
        r"กล่อง"
        r")"
        r"\s*[-]?\s*"
        r"(?P<number>\d{3,})",
        flags=re.IGNORECASE,
    )

    prepared_text = product_model_pattern.sub(
        replace_product_model_number,
        prepared_text,
    )

    prepared_text = improve_thai_spacing(
        prepared_text
    )

    prepared_text = prepared_text.replace(
        ":",
        " ",
    )
    prepared_text = prepared_text.replace(
        ";",
        " ",
    )
    prepared_text = prepared_text.replace(
        "(",
        " ",
    )
    prepared_text = prepared_text.replace(
        ")",
        " ",
    )

    prepared_text = re.sub(
        r"\s+",
        " ",
        prepared_text,
    )

    return prepared_text.strip()


def create_voice(text: str) -> Path:
    """สร้างไฟล์เสียง MP3 จากข้อความ."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "ไม่พบ OPENAI_API_KEY ในไฟล์ .env"
        )

    prepared_text = prepare_text(text)

    if not prepared_text:
        raise ValueError(
            "ไม่มีข้อความสำหรับสร้างเสียง"
        )

    AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if VOICE_FILE.exists():
        VOICE_FILE.unlink()

    logger.info(
        "กำลังสร้างเสียงด้วย OpenAI Marin"
    )
    logger.info(
        "ข้อความสำหรับเสียง: %s",
        prepared_text,
    )

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=prepared_text,
        instructions=VOICE_INSTRUCTIONS,
        speed=TTS_SPEED,
        response_format="mp3",
    ) as response:
        response.stream_to_file(
            VOICE_FILE
        )

    if (
        not VOICE_FILE.exists()
        or VOICE_FILE.stat().st_size == 0
    ):
        raise RuntimeError(
            "OpenAI ไม่ได้สร้างไฟล์เสียง"
        )

    return VOICE_FILE


def play_voice(file_path: Path) -> None:
    """เล่นไฟล์เสียงออกทางลำโพงจนจบ."""

    pygame.mixer.init()

    try:
        pygame.mixer.music.load(
            str(file_path)
        )

        pygame.mixer.music.play()

        clock = pygame.time.Clock()

        while pygame.mixer.music.get_busy():
            clock.tick(20)

        pygame.time.wait(250)

    finally:
        try:
            pygame.mixer.music.unload()
        finally:
            pygame.mixer.quit()

    logger.info(
        "เล่นเสียงเสร็จแล้ว"
    )


def speak(text: str) -> None:
    """สร้างและเล่นเสียงจากข้อความ."""

    if not text.strip():
        return

    voice_file = create_voice(text)
    play_voice(voice_file)