"""โหลด Prompt จากไฟล์ข้อความ."""

from pathlib import Path

from config.settings import PROJECT_ROOT


PROMPT_DIR = PROJECT_ROOT / "prompt"


def load_prompt(filename: str) -> str:
    """
    โหลด Prompt จากโฟลเดอร์ prompt

    Parameters
    ----------
    filename:
        ชื่อไฟล์ เช่น voice_prompt.txt

    Returns
    -------
    str
        เนื้อหา Prompt
    """

    prompt_file = PROMPT_DIR / filename

    if not prompt_file.exists():
        raise FileNotFoundError(
            f"ไม่พบไฟล์ Prompt : {prompt_file}"
        )

    return prompt_file.read_text(
        encoding="utf-8"
    ).strip()