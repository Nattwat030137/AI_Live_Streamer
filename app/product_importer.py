"""Import the complete product catalog into runtime SQLite."""

from app.catalog.init_product_db import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_EXCEL_PATH,
    DEFAULT_JSON_PATH,
    initialize_database,
)


EXCEL_FILE = DEFAULT_EXCEL_PATH
JSON_FILE = DEFAULT_JSON_PATH
DATABASE_FILE = DEFAULT_DATABASE_PATH


def import_products() -> int:
    """Build the runtime catalog from curated JSON and Excel."""

    return initialize_database(
        json_path=JSON_FILE,
        excel_path=EXCEL_FILE,
        database_path=DATABASE_FILE,
    )


def main() -> None:
    """Import products and display a safe summary."""

    print(
        "กำลังนำเข้าสินค้าจาก "
        "JSON และ Excel..."
    )

    imported_count = import_products()

    print("=" * 60)
    print("นำเข้าสินค้าสำเร็จ")
    print(
        "จำนวนสินค้าในฐานข้อมูล: "
        f"{imported_count:,}"
    )
    print(
        f"ฐานข้อมูล: {DATABASE_FILE}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()