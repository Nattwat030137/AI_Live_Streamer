"""Regression tests for Product Attribute Classifier."""

from app.product_attribute import (
    ProductAttribute,
    detect_product_attribute,
)


def check(
    name: str,
    actual: ProductAttribute,
    expected: ProductAttribute,
) -> bool:
    passed = actual == expected
    status = "PASS" if passed else "FAIL"

    print(f"{name:.<35}{status}")

    if not passed:
        print(f"  Expected: {expected.value}")
        print(f"  Actual:   {actual.value}")

    return passed


def main() -> None:
    print("=" * 60)
    print("Product Attribute Regression Test")
    print("=" * 60)

    results = [
        check(
            "Detect color",
            detect_product_attribute("สีอะไร"),
            ProductAttribute.COLOR,
        ),
        check(
            "Detect material",
            detect_product_attribute("วัสดุอะไร"),
            ProductAttribute.MATERIAL,
        ),
        check(
            "Detect produced from",
            detect_product_attribute("ผลิตจากอะไร"),
            ProductAttribute.MATERIAL,
        ),
        check(
            "Detect compatible bag",
            detect_product_attribute("ใช้ถุงอะไร"),
            ProductAttribute.BAG,
        ),
        check(
            "Detect bag size",
            detect_product_attribute("ขนาดถุงเท่าไร"),
            ProductAttribute.BAG,
        ),
        check(
            "Detect seal bag phrase",
            detect_product_attribute(
                "ถาด5073 ใช้กับถุงซีลขนาดเท่าไหร่"
            ),
            ProductAttribute.BAG,
        ),
        check(
            "Detect category",
            detect_product_attribute("อยู่หมวดอะไร"),
            ProductAttribute.CATEGORY,
        ),
        check(
            "Detect full name",
            detect_product_attribute("ชื่อเต็มอะไร"),
            ProductAttribute.NAME,
        ),
        check(
            "Detect note",
            detect_product_attribute("มีหมายเหตุอะไร"),
            ProductAttribute.NOTE,
        ),
        check(
            "Detect general product question",
            detect_product_attribute("5073 คืออะไร"),
            ProductAttribute.GENERAL,
        ),
    ]

    passed_count = sum(results)
    total_count = len(results)

    print("=" * 60)
    print(f"{passed_count} / {total_count} PASSED")
    print("=" * 60)

    if passed_count != total_count:
        raise SystemExit(1)

def test_detects_seal_bag_phrase() -> None:
    assert detect_product_attribute(
        "ถาด5073 ใช้กับถุงซีลขนาดเท่าไหร่"
    ) is ProductAttribute.BAG


if __name__ == "__main__":
    main()
