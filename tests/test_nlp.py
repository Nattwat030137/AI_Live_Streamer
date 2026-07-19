"""ทดสอบ NLP Core."""

from app.nlp import (
    contains_whole_word,
    extract_models,
    keyword_score,
    normalize_text,
    remove_stop_words,
)


def main() -> None:
    """ตรวจการทำงานหลักของ NLP Core."""

    assert normalize_text(
        "  รุ่น 5040  "
    ) == "รุ่น 5040"

    assert extract_models(
        "มีถ้วยรุ่น 5040 และ 5045"
    ) == [
        "5040",
        "5045",
    ]

    assert remove_stop_words(
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    ) == "ถ้วยคัพเค้กรุ่น 5040"

    assert contains_whole_word(
        "ใส่เค้กวันเกิด",
        "ใส",
    ) is False

    assert keyword_score(
        "5040",
        "5040",
    ) == 100

    assert keyword_score(
        "รุ่น 5040",
        "5040",
    ) == 90

    print("=" * 60)
    print("NLP Core ผ่านการทดสอบทั้งหมด")
    print("=" * 60)


if __name__ == "__main__":
    main()