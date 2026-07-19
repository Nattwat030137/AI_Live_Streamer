"""ทดสอบ Intent Engine."""

from app.intent_engine import detect_intent


def main() -> None:
    tests = [
        ("มีถ้วยคัพเค้กไหม", "product"),
        ("ราคาเท่าไร", "price"),
        ("มีของไหม", "stock"),
        ("ใช้ขนส่งอะไร", "shipping"),
        ("รับเองได้ไหม", "store"),
    ]

    for text, expected in tests:
        result = detect_intent(text).value
        print(text, "->", result)
        assert result == expected

    print("=" * 60)
    print("Intent Engine ผ่านการทดสอบทั้งหมด")
    print("=" * 60)


if __name__ == "__main__":
    main()