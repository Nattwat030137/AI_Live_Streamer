"""ทดสอบระบบโหลด Voice Prompt."""

from app.prompt_loader import load_prompt


def main() -> None:
    """โหลดและแสดงเนื้อหา Voice Prompt."""

    voice_prompt = load_prompt(
        "voice_prompt.txt"
    )

    print("=" * 60)
    print("โหลด Voice Prompt สำเร็จ")
    print(f"จำนวนตัวอักษร: {len(voice_prompt)}")
    print("=" * 60)
    print(voice_prompt)
    print("=" * 60)


if __name__ == "__main__":
    main()