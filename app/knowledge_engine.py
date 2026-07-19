"""ระบบอ่านฐานความรู้ของร้านจากไฟล์ JSON."""

import json
from typing import Any

from config.settings import PROJECT_ROOT


KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
PRODUCTS_DIR = KNOWLEDGE_DIR / "products"


def load_json_file(filename: str) -> Any:
    """อ่านไฟล์ JSON หนึ่งไฟล์จากโฟลเดอร์ knowledge."""

    file_path = KNOWLEDGE_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"ไม่พบไฟล์ฐานความรู้: {file_path}"
        )

    with file_path.open(
        mode="r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_all_products() -> list[dict[str, Any]]:
    """อ่านสินค้าจากไฟล์ JSON ทุกไฟล์ในโฟลเดอร์ products."""

    if not PRODUCTS_DIR.exists():
        raise FileNotFoundError(
            f"ไม่พบโฟลเดอร์สินค้า: {PRODUCTS_DIR}"
        )

    all_products: list[dict[str, Any]] = []

    for file_path in sorted(PRODUCTS_DIR.glob("*.json")):
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            product_data = json.load(file)

        products = product_data.get("products", [])

        if not isinstance(products, list):
            raise ValueError(
                f"ข้อมูล products ในไฟล์ {file_path.name} ต้องเป็นรายการ"
            )

        all_products.extend(products)

    return all_products


def load_all_knowledge() -> dict[str, Any]:
    """อ่านข้อมูลร้านทั้งหมดจากโฟลเดอร์ knowledge."""

    return {
        "brand": load_json_file("brand.json"),
        "personality": load_json_file("personality.json"),
        "store": load_json_file("store.json"),
        "shipping": load_json_file("shipping.json"),
        "categories": load_json_file("categories.json"),
        "products": load_all_products(),
    }