"""Regression tests สำหรับ SQLiteProductRepository."""

from __future__ import annotations

from app.catalog.sqlite_repository import (
    ProductRecord,
    SQLiteProductRepository,
)


def assert_product(
    product: ProductRecord | None,
    *,
    expected_model: str,
    expected_name_keyword: str,
) -> ProductRecord:
    """ตรวจข้อมูล ProductRecord พื้นฐาน."""

    assert product is not None, (
        f"ไม่พบสินค้า model={expected_model!r}"
    )

    assert product.model == expected_model, (
        f"model ไม่ตรง: {product.model!r}"
    )

    assert expected_name_keyword in product.name, (
        f"name ไม่พบคำว่า "
        f"{expected_name_keyword!r}: "
        f"{product.name!r}"
    )

    return product


def main() -> None:
    """รัน Regression Test ของ SQLite Repository."""

    repository = SQLiteProductRepository()

    print("=" * 60)
    print("SQLite Product Repository Regression Test")
    print("=" * 60)

    passed = 0
    total = 8

    count = repository.count()

    assert count == 2, (
        f"คาดว่าสินค้า 2 รายการ แต่พบ {count}"
    )

    passed += 1
    print("Count..............................PASS")

    product_5040 = assert_product(
        repository.get_by_model("5040"),
        expected_model="5040",
        expected_name_keyword="คัพเค้ก",
    )

    assert product_5040.material == "กระดาษ"
    assert product_5040.color == "ขาวและน้ำตาล"

    passed += 1
    print("Get model 5040.....................PASS")

    product_5073 = assert_product(
        repository.get_by_model("5073"),
        expected_model="5073",
        expected_name_keyword="ถาดเบเกอรี่",
    )

    assert product_5073.compatible_bag == (
        "12 x 20 ซม."
    )

    passed += 1
    print("Get model 5073.....................PASS")

    missing_product = repository.get_by_model(
        "9999"
    )

    assert missing_product is None

    passed += 1
    print("Missing model......................PASS")

    search_results = repository.search(
        "ถ้วย"
    )

    assert len(search_results) == 1
    assert search_results[0].model == "5040"

    passed += 1
    print("Search.............................PASS")

    all_products = repository.list_all()

    assert [
        product.model
        for product in all_products
    ] == [
        "5040",
        "5073",
    ]

    passed += 1
    print("List all...........................PASS")

    assert repository.exists("5040") is True
    assert repository.exists("9999") is False

    passed += 1
    print("Exists.............................PASS")

    many_products = repository.get_many_by_models(
        (
            "5073",
            "5040",
            "9999",
        )
    )

    assert [
        product.model
        for product in many_products
    ] == [
        "5073",
        "5040",
    ]

    passed += 1
    print("Get many models....................PASS")

    print("=" * 60)
    print(
        f"{passed} / {total} PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
