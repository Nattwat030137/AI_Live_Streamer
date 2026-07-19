"""ทดสอบ Recommendation Engine."""

from pprint import pprint

from app.recommendation_engine import (
    build_search_keywords,
)


def main() -> None:
    tests = [
        "มีถ้วยคัพเค้กไหม",
        "ทำบราวนี่",
        "ห่อคุกกี้",
        "ใส่เค้กวันเกิด",
    ]

    for text in tests:
        print("=" * 50)
        print(text)

        keywords = build_search_keywords(text)

        pprint(keywords)

        assert isinstance(keywords, list)
        assert len(keywords) > 0

    print("=" * 60)
    print("Recommendation Engine ผ่านการทดสอบทั้งหมด")
    print("=" * 60)


if __name__ == "__main__":
    main()