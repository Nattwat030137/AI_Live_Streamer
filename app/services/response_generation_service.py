"""Service for prompt building and LLM response generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.llm.base import LLMProvider
from app.llm.types import (
    LLMRequest,
    LLMResponse,
)
from app.prompt.builder import (
    CommercePromptBuilder,
    PromptBuildResult,
)
from app.search_planner import (
    SearchPlan,
    search_plan_to_dict,
)
from app.services.product_knowledge_service import (
    KnowledgeResult,
)


@dataclass(slots=True)
class ResponseGenerationResult:
    """Typed output from response generation."""

    prompt: PromptBuildResult
    request: LLMRequest
    response: LLMResponse


class ResponseGenerationService:
    """Build a commerce prompt and call an LLM provider."""

    def __init__(
        self,
        *,
        provider: LLMProvider,
        prompt_builder: (
            CommercePromptBuilder | None
        ) = None,
    ) -> None:
        """Initialize with explicit provider dependencies."""

        self.provider = provider
        self.prompt_builder = (
            prompt_builder
            or CommercePromptBuilder()
        )
    def generate(
        self,
        *,
        customer_message: str,
        platform: str,
        knowledge: KnowledgeResult,
        search_plan: SearchPlan,
        conversation_context: str = "",
        product_context: str = "",
        product_attribute: str = "general",
        response_style: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResponseGenerationResult:
        """Build the request and generate one LLM response."""

        normalized_message = (
            customer_message.strip()
        )

        if not normalized_message:
            raise ValueError(
                "customer_message must not be empty"
            )

        normalized_platform = (
            platform.strip().lower() or "unknown"
        )

        prompt_result = self.prompt_builder.build(
            customer_message=normalized_message,
            platform=normalized_platform,
            knowledge=knowledge,
            search_plan=search_plan,
            conversation_context=(
                conversation_context
            ),
            product_context=product_context,
            response_style=response_style,
        )

        request_metadata = dict(
            metadata or {}
        )

        request_metadata.update(
            {
                "knowledge": knowledge,
                "product_attribute": (
                    product_attribute
                ),
                "platform": normalized_platform,
                "search_plan": (
                    search_plan_to_dict(
                        search_plan
                    )
                ),
                "prompt_builder": (
                    prompt_result.to_dict()
                ),
            }
        )
        request = LLMRequest(
            prompt=prompt_result.prompt,
            customer_message=normalized_message,
            system_message=(
                prompt_result.system_message
            ),
            metadata=request_metadata,
        )

        response = self.provider.generate(
            request
        )

        return ResponseGenerationResult(
            prompt=prompt_result,
            request=request,
            response=response,
        )    