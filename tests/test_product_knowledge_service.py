"""Tests for the application product-knowledge service."""

from app.search_planner import create_search_plan
from app.services import (
    KnowledgeResult,
    ProductCatalogRetriever,
    ProductKnowledge,
)
from demo.knowledge_retriever import (
    KnowledgeResult as DemoKnowledgeResult,
)
from demo.knowledge_retriever import (
    ProductCatalogRetriever as DemoProductCatalogRetriever,
)


def test_retriever_finds_product_5040() -> None:
    plan = create_search_plan(
        "มีถ้วยคัพเค้กรุ่น 5040 ไหม"
    )

    result = ProductCatalogRetriever().retrieve(
        plan
    )

    assert isinstance(result, KnowledgeResult)
    assert result.found is True
    assert result.searched_models == ["5040"]

    product = result.primary_product

    assert isinstance(product, ProductKnowledge)
    assert product.model == "5040"
    assert "คัพเค้ก" in product.name
    assert product.material == "กระดาษ"


def test_retriever_reports_missing_product() -> None:
    plan = create_search_plan(
        "มีสินค้ารุ่น 9999 ไหม"
    )

    result = ProductCatalogRetriever().retrieve(
        plan
    )

    assert result.found is False
    assert result.products == []
    assert result.searched_models == ["9999"]
    assert result.warnings


def test_demo_imports_are_compatible() -> None:
    assert (
        DemoProductCatalogRetriever
        is ProductCatalogRetriever
    )
    assert DemoKnowledgeResult is KnowledgeResult