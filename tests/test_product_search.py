"""ทดสอบระบบค้นหาสินค้าแบบอัตโนมัติ."""

from app.product_search import (
    clean_search_keyword,
    search_products,
)


def main() -> None:
    """ตรวจการทำงานหลักของ Product Search."""

    cleaned_keyword = clean_search_keyword(
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    )

    assert "ถ้วยคัพเค้ก" in cleaned_keyword
    assert "5040" in cleaned_keyword

    cupcake_results = search_products(
        "มีถ้วยคัพเค้กไหม",
        limit=5,
    )

    assert cupcake_results
    assert len(cupcake_results) <= 5

    model_results = search_products(
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม",
        limit=5,
    )

    assert model_results

    model_text = " ".join(
        str(product.get("product_name", ""))
        for product in model_results
    )

    assert "5040" in model_text

    unknown_results = search_products(
        "เครื่องชงกาแฟอัตโนมัติรุ่นที่ไม่มีจริง",
        limit=5,
    )

    assert isinstance(
        unknown_results,
        list,
    )

    print("=" * 60)
    print("Product Search ผ่านการทดสอบทั้งหมด")
    print(
        f"ค้นพบถ้วยคัพเค้ก: "
        f"{len(cupcake_results)} รายการ"
    )
    print(
        f"ค้นพบรุ่น 5040: "
        f"{len(model_results)} รายการ"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()