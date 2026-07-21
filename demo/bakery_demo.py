"""Bakery D'Ver AI Commerce OS Demo."""

from __future__ import annotations

import sys
from time import perf_counter
from dataclasses import dataclass
from typing import Any

from app.services import (
    CommercePipelineResult,
    CommerceService,
    ResponseGenerationService,
)
from app.memory.conversation import ConversationMemory
from app.memory.product_slots import ProductSlots
from app.policies.engine import GovernanceEngine
from app.policies.registry import PolicyRegistry
from app.llm.factory import create_llm_provider
from demo.renderer import (
    ConsoleRenderer,
    DemoReport,
)
from demo.sample_data import (
    DEMO_SCENARIOS,
    DemoScenario,
    get_scenario,
)


INTENT_BY_RULE: dict[str, tuple[str, int]] = {

      "PRODUCT_CATALOG_COMPATIBLE_BAG": (
        "product_information",
        95,
    ),
    "PRODUCT_CATALOG": (
        "product_information",
        92,
    ),
    "PRODUCT_CATALOG_MISSING_BAG": (
        "information",
        85,
    ),
    "PRODUCT_MODEL_5040": (
        "information",
        92,
    ),
    "PRICE_REQUEST": (
        "information",
        88,
    ),
    "STOCK_REQUEST": (
        "buying",
        90,
    ),
    "SHIPPING_REQUEST": (
        "information",
        84,
    ),
    "THANK_YOU": (
        "acknowledgement",
        80,
    ),
    "DEFAULT": (
        "information",
        55,
    ),
}


EMOTION_BY_RULE: dict[str, tuple[str, int]] = {

        "PRODUCT_CATALOG_COMPATIBLE_BAG": (
        "interested",
        78,
    ),
    "PRODUCT_CATALOG": (
        "interested",
        72,
    ),
    "PRODUCT_CATALOG_MISSING_BAG": (
        "neutral",
        55,
    ),
    "PRODUCT_MODEL_5040": (
        "interested",
        75,
    ),
    "PRICE_REQUEST": (
        "interested",
        68,
    ),
    "STOCK_REQUEST": (
        "interested",
        72,
    ),
    "SHIPPING_REQUEST": (
        "neutral",
        50,
    ),
    "THANK_YOU": (
        "positive",
        82,
    ),
    "DEFAULT": (
        "neutral",
        40,
    ),
}


STRATEGY_BY_RULE: dict[str, str] = {

        "PRODUCT_CATALOG_COMPATIBLE_BAG": (
        "answer_compatible_packaging"
    ),
    "PRODUCT_CATALOG": (
        "answer_product_information"
    ),
    "PRODUCT_CATALOG_MISSING_BAG": (
        "human_handoff_for_product_detail"
    ),
    "PRODUCT_MODEL_5040": (
        "answer_product_information"
    ),
    "PRICE_REQUEST": (
        "human_handoff_for_price"
    ),
    "STOCK_REQUEST": (
        "human_handoff_for_stock"
    ),
    "SHIPPING_REQUEST": (
        "answer_shipping_information"
    ),
    "THANK_YOU": (
        "acknowledge_customer"
    ),
    "DEFAULT": (
        "request_more_information"
    ),
}

@dataclass(slots=True)
class PreparedContext:
    pipeline: CommercePipelineResult
    resolved_models: list[str]
    search_plan: Any
    search_plan_data: dict[str, Any]
    product_attribute: Any
    knowledge_result: Any

class BakeryDemo:
    """ประสานงานส่วนต่าง ๆ ของ Bakery Demo."""

    def __init__(
        self,
        *,
        provider_name: str = "mock",
        provider_options: dict[str, Any] | None = None,
    ) -> None:
        """สร้าง Component ที่ Demo ต้องใช้."""

        resolved_provider_options = (
            provider_options
            if provider_options is not None
            else {}
        )

        self.llm = create_llm_provider(
            provider_name,
            **resolved_provider_options,
        )

        self.response_generation = (
            ResponseGenerationService(
                provider=self.llm,
            )
        )

        self.renderer = ConsoleRenderer()

        self.registry = PolicyRegistry()

        self.governance = GovernanceEngine(
            registry=self.registry,
        )
        self.memory = ConversationMemory()
        self.product_slots = ProductSlots()
        self.commerce_service = CommerceService(
            memory=self.memory,
            response_generation_service=(
                self.response_generation
            ),
            governance_engine=self.governance,
        )

    def _prepare_context(
        self,
        scenario: DemoScenario,
    ) -> PreparedContext:
        """Prepare the shared commerce pipeline once."""

        pipeline = (
            self.commerce_service.prepare_pipeline(
                customer_message=(
                    scenario.customer_message
                ),
                platform=scenario.platform,
            )
        )

        planning = pipeline.planning

        return PreparedContext(
            pipeline=pipeline,
            resolved_models=list(
                planning.resolved_models
            ),
            search_plan=planning.search_plan,
            search_plan_data=(
                planning.search_plan_data
            ),
            product_attribute=(
                pipeline.product_attribute
            ),
            knowledge_result=(
                pipeline.knowledge
            ),
        )
    def run_scenario(
        self,
        scenario: DemoScenario,
    ) -> DemoReport:
        """ประมวลผล Scenario หนึ่งรายการ."""

        started_at = perf_counter()

        prepared = self._prepare_context(
            scenario
        )

        search_plan = prepared.search_plan

        resolved_models = (
            prepared.resolved_models
        )

        search_plan_data = (
            prepared.search_plan_data
        )

        product_attribute = (
            prepared.product_attribute
        )

        knowledge_result = (
            prepared.knowledge_result
        )

        primary_product = (
            knowledge_result.primary_product
        )

        if primary_product is not None:
            self.product_slots.update(
                model=primary_product.model,
                name=primary_product.name,
                category=primary_product.category,
                material=primary_product.material,
                color=primary_product.color,
                bag_size=(
                    primary_product.compatible_bag
                ),
                notes=primary_product.notes,
                extra={
                    "source": (
                        primary_product.source
                    ),
                },
            )

        commerce_response = (
            self.commerce_service
            .process_prepared_pipeline(
                prepared.pipeline,
                product_context=(
                    self.product_slots
                    .build_context_text()
                ),
                metadata={
                    "scenario_id": (
                        scenario.scenario_id
                    ),
                },
            )
        )

        llm_data = commerce_response.metadata[
            "llm"
        ]
        prompt_data = commerce_response.metadata[
            "prompt_builder"
        ]
        governance_data = (
            commerce_response.metadata[
                "governance"
            ]
        )

        if not isinstance(llm_data, dict):
            raise RuntimeError(
                "Commerce response is missing LLM data."
            )

        if not isinstance(prompt_data, dict):
            raise RuntimeError(
                "Commerce response is missing prompt data."
            )

        if not isinstance(governance_data, dict):
            raise RuntimeError(
                "Commerce response is missing governance data."
            )

        prompt = str(prompt_data["prompt"])
        llm_reply = str(llm_data["text"])
        llm_model = str(llm_data["model"])
        matched_rule = str(
            llm_data["matched_rule"]
        )

        intent, intent_score = (
            INTENT_BY_RULE.get(
                matched_rule,
                (
                    "unknown",
                    0,
                ),
            )
        )

        emotion, emotion_score = (
            EMOTION_BY_RULE.get(
                matched_rule,
                (
                    "neutral",
                    0,
                ),
            )
        )

        strategy = STRATEGY_BY_RULE.get(
            matched_rule,
            "answer",
        )

        self.memory.update_context(
            topic=matched_rule,
            intent=intent,
        )

        elapsed_ms = (
            perf_counter() - started_at
        ) * 1000

        return DemoReport(
            customer_message=(
                scenario.customer_message
            ),
            platform=scenario.platform,
            intent=intent,
            intent_score=intent_score,
            emotion=emotion,
            emotion_score=emotion_score,
            strategy=strategy,
            product_attribute=(
                product_attribute.value
            ),
            extracted_models=list(
                resolved_models
            ),
            extracted_tokens=list(
                search_plan.extracted_tokens
            ),
            search_tasks=list(
                search_plan_data["tasks"]
            ),
            prompt_summary=prompt,
            llm_reply=llm_reply,
            llm_model=llm_model,
            matched_rule=matched_rule,
            governance_allowed=(
                commerce_response.allowed
            ),
            risk_score=(
                commerce_response.risk_score
            ),
            compliance_score=(
                commerce_response.compliance_score
            ),
            final_reply=commerce_response.text,
            execution_time_ms=elapsed_ms,
            warnings=list(
                governance_data["warnings"]
            ),
            metadata={
                "scenario_id": (
                    scenario.scenario_id
                ),
                "expected_rule": (
                    scenario.expected_rule
                ),
                "search_plan": (
                    search_plan_data
                ),
                "governance": governance_data,
            },
        )

    def run_all(self) -> None:
        """รัน Scenario ทั้งหมด."""

        for index, scenario in enumerate(
            DEMO_SCENARIOS,
            start=1,
        ):
            if index > 1:
                print()

            report = self.run_scenario(
                scenario
            )

            self.renderer.render(
                report
            )

    def run_interactive(self) -> None:
        """รับคำถามจากผู้ใช้ผ่าน Console."""

        print()
        print(
            "พิมพ์คำถามลูกค้า "
            "หรือพิมพ์ exit เพื่อออก"
        )

        while True:
            print()

            try:
                customer_message = input(
                    "Customer: "
                ).strip()

            except (
                EOFError,
                KeyboardInterrupt,
            ):
                print()
                break

            if customer_message.lower() in {
                "exit",
                "quit",
                "q",
            }:
                break

            if not customer_message:
                continue

            scenario = DemoScenario(
                scenario_id="interactive",
                title="Interactive Demo",
                customer_message=(
                    customer_message
                ),
                platform="shopee",
            )

            report = self.run_scenario(
                scenario
            )

            print()
            self.renderer.render(
                report
            )


def print_usage() -> None:
    """แสดงวิธีเรียก Demo."""

    print(
        "Usage:\n"
        "  python -m demo.bakery_demo\n"
        "  python -m demo.bakery_demo all\n"
        "  python -m demo.bakery_demo interactive\n"
        "  python -m demo.bakery_demo "
        "<scenario-id>\n"
    )

    print(
        "Scenario IDs:"
    )

    for scenario in DEMO_SCENARIOS:
        print(
            f"  {scenario.scenario_id}"
        )


def main() -> None:
    """Entry point ของ Bakery Demo."""

    demo = BakeryDemo()

    arguments = sys.argv[1:]

    if not arguments:
        scenario = DEMO_SCENARIOS[0]

        demo.renderer.render(
            demo.run_scenario(
                scenario
            )
        )

        return

    command = arguments[0].strip().lower()

    if command == "all":
        demo.run_all()
        return

    if command == "interactive":
        demo.run_interactive()
        return

    if command in {
        "help",
        "--help",
        "-h",
    }:
        print_usage()
        return

    scenario = get_scenario(
        command
    )

    if scenario is None:
        print(
            f"ไม่พบ Scenario: {command}"
        )
        print()
        print_usage()
        raise SystemExit(1)

    demo.renderer.render(
        demo.run_scenario(
            scenario
        )
    )


if __name__ == "__main__":
    main()
