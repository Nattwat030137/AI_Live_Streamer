"""Commerce service for processing customer messages."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.policies.engine import GovernanceEngine
from app.intent_engine import Intent, detect_intent
from app.memory.conversation import ConversationMemory
from app.product_attribute import (
    ProductAttribute,
    detect_product_attribute,
)
from app.services.models import (
    CommerceContext,
    CommerceResponse,
)
from app.services.product_knowledge_service import (
    KnowledgeResult,
    ProductCatalogRetriever,
)
from app.services.response_generation_service import (
    ResponseGenerationService,
)
from app.services.search_planning_service import (
    SearchPlanningResult,
    SearchPlanningService,
)


@dataclass(slots=True)
class CommercePipelineResult:
    """Typed result prepared by the commerce pipeline."""

    customer_message: str
    platform: str
    intent: Intent
    product_attribute: ProductAttribute
    planning: SearchPlanningResult
    knowledge: KnowledgeResult


class CommerceService:
    """
    Transport-independent business service for AI Commerce.

    The service can later be used by Console, LINE, TikTok,
    OBS, or a Web API without changing the response model.
    """

    def __init__(
        self,
        *,
        memory: ConversationMemory | None = None,
        knowledge_retriever: (
            ProductCatalogRetriever | None
        ) = None,
        response_generation_service: (
            ResponseGenerationService | None
        ) = None,
        governance_engine: (
            GovernanceEngine | None
        ) = None,
    ) -> None:
        """Initialize commerce application services."""

        self.memory = memory or ConversationMemory()

        self.search_planning_service = (
            SearchPlanningService(
                memory=self.memory,
            )
        )

        self.knowledge_retriever = (
            knowledge_retriever
            or ProductCatalogRetriever()
        )

        self.response_generation_service = (
            response_generation_service
        )
        self.governance_engine = (
            governance_engine
        )

    def prepare_pipeline(
        self,
        *,
        customer_message: str,
        platform: str = "shopee",
    ) -> CommercePipelineResult:
        """Prepare typed analysis, search, and knowledge data."""

        message = customer_message.strip()

        if not message:
            raise ValueError(
                "Cannot prepare commerce pipeline "
                "for an empty customer message."
            )

        selected_platform = (
            platform.strip().lower() or "shopee"
        )

        intent = detect_intent(message)
        product_attribute = detect_product_attribute(
            message
        )

        planning = self.search_planning_service.prepare(
            customer_message=message,
        )

        knowledge = self.knowledge_retriever.retrieve(
            planning.resolved_search_plan
        )

        resolved_models = list(
            planning.resolved_models
        )

        self.memory.add_customer(
            message,
            metadata={
                "models": resolved_models,
                "intent": intent.value,
                "product_attribute": (
                    product_attribute.value
                ),
                "platform": selected_platform,
                "knowledge_found": knowledge.found,
            },
        )

        self.memory.update_context(
            intent=intent.value,
        )

        return CommercePipelineResult(
            customer_message=message,
            platform=selected_platform,
            intent=intent,
            product_attribute=product_attribute,
            planning=planning,
            knowledge=knowledge,
        )

    def prepare_context(
        self,
        *,
        message: str,
        platform: str = "shopee",
    ) -> CommerceContext:
        """Prepare typed intent and product-attribute context."""

        pipeline = self.prepare_pipeline(
            customer_message=message,
            platform=platform,
        )

        return CommerceContext(
            intent=pipeline.intent,
            product_attribute=(
                pipeline.product_attribute
            ),
        )

    def process_prepared_pipeline(
        self,
        pipeline: CommercePipelineResult,
        *,
        product_context: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> CommerceResponse:
        """Generate a response from a prepared pipeline."""

        return self.process_message(
            pipeline.customer_message,
            platform=pipeline.platform,
            product_context=product_context,
            metadata=metadata,
            _prepared_pipeline=pipeline,
        )

    def process_message(
        self,
        customer_message: str,
        platform: str = "shopee",
        *,
        product_context: str = "",
        metadata: dict[str, Any] | None = None,
        _prepared_pipeline: (
            CommercePipelineResult | None
        ) = None,
    ) -> CommerceResponse:
        """Process a message and return serializable metadata."""

        started_at = perf_counter()

        message = customer_message.strip()
        selected_platform = (
            platform.strip().lower() or "shopee"
        )
        request_metadata = dict(
            metadata or {}
        )

        if not message:
            elapsed_ms = (
                perf_counter() - started_at
            ) * 1000

            return CommerceResponse(
                text="กรุณาระบุข้อความของลูกค้า",
                allowed=False,
                risk_score=0.0,
                compliance_score=100.0,
                execution_time_ms=elapsed_ms,
                metadata={
                    "platform": selected_platform,
                    "status": "empty_message",
                },
            )

        if _prepared_pipeline is None:
            pipeline = self.prepare_pipeline(
                customer_message=message,
                platform=selected_platform,
            )
        else:
            pipeline = _prepared_pipeline
            message = pipeline.customer_message
            selected_platform = pipeline.platform

        planning = pipeline.planning
        knowledge = pipeline.knowledge
        primary_product = knowledge.primary_product

        response_text = "CommerceService is ready."
        generation_status = "disabled"
        governance_status = "disabled"
        llm_data = None
        prompt_data = None
        governance_data = None
        response_status = "intent_analyzed"
        allowed = True
        risk_score = 0.0
        compliance_score = 100.0

        if self.response_generation_service is not None:
            generation = (
                self.response_generation_service.generate(
                    customer_message=message,
                    platform=selected_platform,
                    knowledge=knowledge,
                    search_plan=(
                        planning.resolved_search_plan
                    ),
                    conversation_context=(
                        self.memory.build_context_text()
                    ),
                    product_context=product_context,
                    product_attribute=(
                        pipeline.product_attribute.value
                    ),
                    metadata=(
                        request_metadata or None
                    ),
                )
            )

            response_text = generation.response.text
            generation_status = "generated"
            llm_data = generation.response.to_dict()
            prompt_data = generation.prompt.to_dict()
            response_status = "response_generated"

            if self.governance_engine is not None:
                governance_result = (
                    self.governance_engine.evaluate_reply(
                        reply=response_text,
                        platform=selected_platform,
                        customer_message=message,
                        metadata={
                            **request_metadata,
                            "mock_rule": (
                                generation
                                .response
                                .matched_rule
                            ),
                            "search_plan": (
                                planning.search_plan_data
                            ),
                            "intent": (
                                pipeline.intent.value
                            ),
                            "product_attribute": (
                                pipeline
                                .product_attribute
                                .value
                            ),
                        },
                    )
                )

                response_text = (
                    governance_result.sanitized_reply
                )
                governance_status = "evaluated"
                governance_data = (
                    governance_result.to_dict()
                )
                allowed = governance_result.allowed
                risk_score = float(
                    governance_result.risk_score
                )
                compliance_score = float(
                    governance_result.compliance_score
                )
                response_status = (
                    "governance_evaluated"
                )

            self.memory.add_assistant(
                response_text
            )

        elapsed_ms = (
            perf_counter() - started_at
        ) * 1000

        return CommerceResponse(
            text=response_text,
            allowed=allowed,
            risk_score=risk_score,
            compliance_score=compliance_score,
            execution_time_ms=elapsed_ms,
            metadata={
                "customer_message": message,
                "platform": selected_platform,
                "request_metadata": request_metadata,
                "intent": pipeline.intent.value,
                "product_attribute": (
                    pipeline.product_attribute.value
                ),
                "resolved_models": list(
                    planning.resolved_models
                ),
                "search_plan": (
                    planning.search_plan_data
                ),
                "search_status": "prepared",
                "knowledge": knowledge.to_dict(),
                "knowledge_found": knowledge.found,
                "knowledge_status": (
                    "found"
                    if knowledge.found
                    else "not_found"
                ),
                "primary_product": (
                    primary_product.to_dict()
                    if primary_product is not None
                    else None
                ),
                "generation_status": (
                    generation_status
                ),
                "governance_status": (
                    governance_status
                ),
                "governance": governance_data,
                "llm": llm_data,
                "prompt_builder": prompt_data,
                "status": response_status,
            },
        )