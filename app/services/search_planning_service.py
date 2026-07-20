"""Search-planning service for commerce conversations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.memory.conversation import ConversationMemory
from app.memory.reference_resolver import resolve_reference
from app.search_planner import (
    clone_search_plan_with_models,
    create_search_plan,
    search_plan_to_dict,
)


@dataclass(slots=True)
class SearchPlanningResult:
    """Prepared search-planning data for one customer message."""

    resolved_models: list[str]
    search_plan: Any
    resolved_search_plan: Any
    search_plan_data: dict[str, Any]


class SearchPlanningService:
    """Prepare search plans using conversation memory and references."""

    def __init__(
        self,
        *,
        memory: ConversationMemory,
    ) -> None:
        self.memory = memory

    def prepare(
        self,
        *,
        customer_message: str,
        max_tasks: int = 10,
        graph_limit_per_task: int = 4,
    ) -> SearchPlanningResult:
        """Build and resolve a search plan for a customer message."""

        search_plan = create_search_plan(
            message=customer_message,
            max_tasks=max_tasks,
            graph_limit_per_task=graph_limit_per_task,
        )

        resolved_models = self.memory.resolve_models(
            search_plan.extracted_models
        )

        reference_model = resolve_reference(
            customer_message,
            self.memory,
        )

        if (
            reference_model is not None
            and reference_model not in resolved_models
        ):
            resolved_models.insert(
                0,
                reference_model,
            )

        self.memory.active_models = resolved_models

        resolved_search_plan = clone_search_plan_with_models(
            plan=search_plan,
            models=resolved_models,
            max_tasks=max_tasks,
            graph_limit_per_task=graph_limit_per_task,
        )

        search_plan_data = search_plan_to_dict(
            resolved_search_plan
        )

        return SearchPlanningResult(
            resolved_models=resolved_models,
            search_plan=search_plan,
            resolved_search_plan=resolved_search_plan,
            search_plan_data=search_plan_data,
        )
