"""ทดสอบว่าโหลดฐานความรู้ครบทุกไฟล์หรือไม่."""

from app.knowledge_engine import load_all_knowledge


def main() -> None:
    knowledge = load_all_knowledge()

    print("=" * 50)

    for key in knowledge:
        print(f"โหลดสำเร็จ : {key}")

    print("=" * 50)


if __name__ == "__main__":
    main()