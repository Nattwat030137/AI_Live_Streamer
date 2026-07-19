"""ทดสอบ Product Intelligence."""

from pprint import pprint

from app.product_intelligence import summarize_products
from app.product_search import search_products


def main() -> None:
    products = search_products("5040", 10)

    summary = summarize_products(products)

    pprint(summary)

    assert summary["count"] > 0
    assert summary["model"] == "5040"

    print("=" * 60)
    print("Product Intelligence ผ่านการทดสอบทั้งหมด")
    print("=" * 60)


if __name__ == "__main__":
    main()