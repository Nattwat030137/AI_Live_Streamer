"""ทดสอบ Product Graph Reader V2."""

from app.product_graph_reader import (
    get_ranked_related_products,
    rank_related_keywords,
)


def main() -> None:
    """ตรวจ Keyword และสินค้าที่เกี่ยวข้อง."""

    cupcake_keywords = rank_related_keywords(
        query="คัพเค้ก",
        limit=10,
        minimum_score=60,
    )

    assert cupcake_keywords
    assert cupcake_keywords[0][0] == "คัพเค้ก"

    birthday_keywords = rank_related_keywords(
        query="ใส่เค้กวันเกิด",
        limit=20,
        minimum_score=60,
    )

    birthday_keyword_names = [
        keyword
        for keyword, _ in birthday_keywords
    ]

    assert "ใส" not in birthday_keyword_names

    products = get_ranked_related_products(
        keyword="คัพเค้ก",
        keyword_limit=10,
        product_limit=5,
    )

    assert products

    print("=" * 60)
    print("Product Graph Reader V2 ผ่านการทดสอบ")
    print("=" * 60)

    print("Keyword คัพเค้ก:")
    for keyword, score in cupcake_keywords:
        print(
            f"- {keyword} | score={score}"
        )

    print("-" * 60)
    print("Keyword ใส่เค้กวันเกิด:")
    for keyword, score in birthday_keywords:
        print(
            f"- {keyword} | score={score}"
        )

    print("-" * 60)
    print(
        f"พบสินค้าคัพเค้ก {len(products)} รายการ"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()