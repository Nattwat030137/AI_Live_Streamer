"""อ่าน Product Graph."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from config.settings import PROJECT_ROOT

from app.nlp import (
    keyword_score,
    normalize_text,
    remove_duplicate,
)

GRAPH_FILE = (
    PROJECT_ROOT
    / "knowledge"
    / "product_graph.json"
)


@lru_cache(maxsize=1)
def load_product_graph() -> dict[str, Any]:
    """โหลด Product Graph."""

    if not GRAPH_FILE.exists():
        raise FileNotFoundError(
            f"ไม่พบไฟล์ {GRAPH_FILE}"
        )

    with GRAPH_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        graph = json.load(file)

    if not isinstance(
        graph,
        dict,
    ):
        raise ValueError(
            "Product Graph ไม่ถูกต้อง"
        )

    return graph


def clear_graph_cache() -> None:
    """ล้าง Cache."""

    load_product_graph.cache_clear()


def get_keyword_index() -> dict[str, list[str]]:
    """คืน Keyword Index."""

    graph = load_product_graph()

    keyword_index = graph.get(
        "keywords",
        {},
    )

    if not isinstance(
        keyword_index,
        dict,
    ):
        return {}

    return keyword_index


def get_product_index() -> dict[str, Any]:
    """คืน Product Index."""

    graph = load_product_graph()

    products = graph.get(
        "products",
        {},
    )

    if not isinstance(
        products,
        dict,
    ):
        return {}

    return products
def rank_related_keywords(
    query: str,
    limit: int = 20,
    minimum_score: int = 60,
) -> list[tuple[str, int]]:
    """จัดอันดับ Keyword ใน Graph ตามความเกี่ยวข้องกับคำค้น."""

    cleaned_query = normalize_text(
        query
    )

    if not cleaned_query or limit <= 0:
        return []

    keyword_index = get_keyword_index()

    ranked_keywords: list[
        tuple[str, int]
    ] = []

    for graph_keyword in keyword_index:
        cleaned_keyword = normalize_text(
            graph_keyword
        )

        if not cleaned_keyword:
            continue

        score = keyword_score(
            query=cleaned_query,
            candidate=cleaned_keyword,
        )

        if score < minimum_score:
            continue

        ranked_keywords.append(
            (
                cleaned_keyword,
                score,
            )
        )

    ranked_keywords.sort(
        key=lambda item: (
            -item[1],
            len(item[0]),
            item[0],
        )
    )

    unique_keywords: list[
        tuple[str, int]
    ] = []

    seen_keywords: set[str] = set()

    for keyword, score in ranked_keywords:
        if keyword in seen_keywords:
            continue

        seen_keywords.add(keyword)

        unique_keywords.append(
            (
                keyword,
                score,
            )
        )

        if len(unique_keywords) >= limit:
            break

    return unique_keywords


def search_related_keywords(
    keyword: str,
    limit: int = 20,
) -> list[str]:
    """คืน Keyword ที่เกี่ยวข้อง เรียงตามคะแนน."""

    ranked_keywords = rank_related_keywords(
        query=keyword,
        limit=limit,
        minimum_score=60,
    )

    return [
        graph_keyword
        for graph_keyword, _ in ranked_keywords
    ]


def get_product_keys_for_keywords(
    keywords: list[str],
    limit: int = 100,
) -> list[str]:
    """คืน Product Key ที่เชื่อมกับ Keyword โดยไม่ให้ซ้ำ."""

    if not keywords or limit <= 0:
        return []

    keyword_index = get_keyword_index()

    product_keys: list[str] = []
    seen_keys: set[str] = set()

    for keyword in keywords:
        related_keys = keyword_index.get(
            keyword,
            [],
        )

        if not isinstance(
            related_keys,
            list,
        ):
            continue

        for product_key in related_keys:
            cleaned_key = normalize_text(
                product_key
            )

            if not cleaned_key:
                continue

            if cleaned_key in seen_keys:
                continue

            seen_keys.add(
                cleaned_key
            )

            product_keys.append(
                cleaned_key
            )

            if len(product_keys) >= limit:
                return product_keys

    return product_keys


def get_product_nodes(
    product_keys: list[str],
) -> list[dict[str, Any]]:
    """คืน Product Node ตาม Product Key."""

    if not product_keys:
        return []

    product_index = get_product_index()

    nodes: list[dict[str, Any]] = []

    for product_key in product_keys:
        node = product_index.get(
            product_key
        )

        if isinstance(
            node,
            dict,
        ):
            nodes.append(node)

    return nodes
def find_related_products(
    keyword: str,
    keyword_limit: int = 20,
    product_limit: int = 20,
) -> list[dict[str, Any]]:
    """ค้นหา Product Node ที่เกี่ยวข้องกับคำค้น."""

    related_keywords = search_related_keywords(
        keyword=keyword,
        limit=keyword_limit,
    )

    product_keys = get_product_keys_for_keywords(
        keywords=related_keywords,
        limit=product_limit,
    )

    return get_product_nodes(
        product_keys
    )


def get_ranked_related_products(
    keyword: str,
    keyword_limit: int = 20,
    product_limit: int = 20,
) -> list[dict[str, Any]]:
    """
    ค้นหาสินค้าที่เกี่ยวข้องพร้อมข้อมูล Keyword และคะแนน

    ผลลัพธ์แต่ละรายการจะมี:
    - product_key
    - matched_keywords
    - best_score
    - product
    """

    if not keyword.strip():
        return []

    ranked_keywords = rank_related_keywords(
        query=keyword,
        limit=keyword_limit,
        minimum_score=60,
    )

    if not ranked_keywords:
        return []

    keyword_index = get_keyword_index()
    product_index = get_product_index()

    product_matches: dict[
        str,
        dict[str, Any],
    ] = {}

    for graph_keyword, score in ranked_keywords:
        related_product_keys = keyword_index.get(
            graph_keyword,
            [],
        )

        if not isinstance(
            related_product_keys,
            list,
        ):
            continue

        for product_key in related_product_keys:
            cleaned_key = normalize_text(
                product_key
            )

            if not cleaned_key:
                continue

            product_node = product_index.get(
                cleaned_key
            )

            if not isinstance(
                product_node,
                dict,
            ):
                continue

            if cleaned_key not in product_matches:
                product_matches[
                    cleaned_key
                ] = {
                    "product_key": cleaned_key,
                    "matched_keywords": [],
                    "best_score": score,
                    "product": product_node,
                }

            match_data = product_matches[
                cleaned_key
            ]

            if graph_keyword not in match_data[
                "matched_keywords"
            ]:
                match_data[
                    "matched_keywords"
                ].append(
                    graph_keyword
                )

            if score > match_data[
                "best_score"
            ]:
                match_data[
                    "best_score"
                ] = score

    ranked_products = list(
        product_matches.values()
    )

    ranked_products.sort(
        key=lambda item: (
            -int(
                item.get(
                    "best_score",
                    0,
                )
            ),
            -len(
                item.get(
                    "matched_keywords",
                    [],
                )
            ),
            str(
                item.get(
                    "product_key",
                    "",
                )
            ),
        )
    )

    return ranked_products[:product_limit]


def print_related_keywords(
    keyword: str,
    limit: int = 20,
) -> None:
    """แสดง Keyword ที่เกี่ยวข้องพร้อมคะแนน."""

    ranked_keywords = rank_related_keywords(
        query=keyword,
        limit=limit,
        minimum_score=60,
    )

    print("=" * 60)
    print(f"คำค้น: {keyword}")
    print("=" * 60)

    if not ranked_keywords:
        print("ไม่พบ Keyword ที่เกี่ยวข้อง")
        print("=" * 60)
        return

    for number, (
        graph_keyword,
        score,
    ) in enumerate(
        ranked_keywords,
        start=1,
    ):
        print(
            f"{number}. "
            f"{graph_keyword!r} | "
            f"score={score}"
        )

    print("=" * 60)


def main() -> None:
    """ทดสอบ Product Graph Reader."""

    keyword = input(
        "คำค้น Product Graph: "
    ).strip()

    print_related_keywords(
        keyword=keyword,
        limit=20,
    )

    ranked_products = get_ranked_related_products(
        keyword=keyword,
        keyword_limit=20,
        product_limit=5,
    )

    print(
        f"พบสินค้า {len(ranked_products)} รายการ"
    )

    for number, item in enumerate(
        ranked_products,
        start=1,
    ):
        product = item.get(
            "product",
            {},
        )

        product_names = product.get(
            "product_names",
            [],
        )

        product_name = (
            product_names[0]
            if isinstance(product_names, list)
            and product_names
            else "ไม่มีชื่อสินค้า"
        )

        print(
            f"{number}. {product_name}"
        )
        print(
            "   Keyword:",
            item.get(
                "matched_keywords",
                [],
            ),
        )
        print(
            "   Score:",
            item.get(
                "best_score",
                0,
            ),
        )

    print("=" * 60)


if __name__ == "__main__":
    main()