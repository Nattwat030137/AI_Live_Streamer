"""Regression tests สำหรับ Response Style Control."""

from app.prompt.style import (
    ResponseStyle,
    parse_response_style,
    resolve_response_style,
    supported_response_styles,
)


def main() -> None:
    """รัน Regression Test ของ Response Style."""

    print("=" * 60)
    print("Response Style Regression Test")
    print("=" * 60)

    passed = 0
    total = 7

    assert parse_response_style("brief") == (
        ResponseStyle.BRIEF
    )
    assert parse_response_style("short") == (
        ResponseStyle.BRIEF
    )

    passed += 1
    print("Parse brief.........................PASS")

    assert parse_response_style("standard") == (
        ResponseStyle.STANDARD
    )
    assert parse_response_style("normal") == (
        ResponseStyle.STANDARD
    )

    passed += 1
    print("Parse standard......................PASS")

    assert parse_response_style("detailed") == (
        ResponseStyle.DETAILED
    )
    assert parse_response_style("full") == (
        ResponseStyle.DETAILED
    )

    passed += 1
    print("Parse detailed......................PASS")

    shopee = resolve_response_style(
        platform="shopee"
    )

    assert shopee.style == ResponseStyle.BRIEF
    assert shopee.max_sentences == 2
    assert shopee.prefer_bullets is False

    passed += 1
    print("Shopee default......................PASS")

    line = resolve_response_style(
        platform="line"
    )

    assert line.style == ResponseStyle.STANDARD
    assert line.prefer_bullets is True

    passed += 1
    print("LINE default........................PASS")

    override = resolve_response_style(
        platform="shopee",
        requested_style="detailed",
    )

    assert override.style == (
        ResponseStyle.DETAILED
    )
    assert override.max_sentences is None

    passed += 1
    print("Style override......................PASS")

    assert supported_response_styles() == (
        "brief",
        "standard",
        "detailed",
    )

    try:
        parse_response_style(
            "unsupported-style"
        )
    except ValueError as error:
        assert "ไม่รองรับ" in str(error)
    else:
        raise AssertionError(
            "Style ที่ไม่รองรับต้องเกิด ValueError"
        )

    passed += 1
    print("Validation..........................PASS")

    print("=" * 60)
    print(f"{passed} / {total} PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
