"""
Compatibility imports for product-knowledge retrieval.

The implementation now lives in the application service layer.
Existing Demo and test imports remain supported.
"""

from app.services.product_knowledge_service import (
    KnowledgeResult,
    ProductCatalogRetriever,
    ProductKnowledge,
)

__all__ = [
    "KnowledgeResult",
    "ProductCatalogRetriever",
    "ProductKnowledge",
]