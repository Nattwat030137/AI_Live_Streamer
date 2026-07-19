"""Console renderer สำหรับ Bakery D'Ver Demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


LINE_WIDTH = 60


@dataclass(slots=True)
class DemoReport:
    """ข้อมูลที่ใช้แสดงผล Demo หนึ่งรอบ."""

    customer_message: str
    platform: str

    intent: str = "unknown"
    intent_score: int = 0
    emotion: str = "neutral"
    emotion_score: int = 0
    strategy: str = "unknown"
    product_attribute: str = "general"

    extracted_models: list[str] = field(
        default_factory=list
    )
    extracted_tokens: list[str] = field(
        default_factory=list
    )
    search_tasks: list[dict[str, Any]] = field(
        default_factory=list
    )

    prompt_summary: str = ""
    llm_reply: str = ""
    llm_model: str = ""
    matched_rule: str = ""

    governance_allowed: bool = True
    risk_score: int = 0
    compliance_score: int = 100

    final_reply: str = ""
    execution_time_ms: float = 0.0

    warnings: list[str] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class ConsoleRenderer:
    """แสดง Demo Report ในรูปแบบ Console."""

    def __init__(
        self,
        *,
        width: int = LINE_WIDTH,
    ) -> None:
        """สร้าง Renderer."""

        self.width = max(
            int(width),
            40,
        )

    def render(
        self,
        report: DemoReport,
    ) -> None:
        """แสดงรายงาน Demo ทั้งหมด."""

        self._print_line("=")
        self._print_center(
            "AI Commerce OS"
        )
        self._print_center(
            "Bakery D'Ver Demo"
        )
        self._print_line("=")

        self._print_section(
            "Customer",
            report.customer_message,
        )

        self._print_section(
            "Platform",
            report.platform,
        )

        self._print_section(
            "Intent",
            (
                f"{report.intent} "
                f"({report.intent_score})"
            ),
        )

        self._print_section(
            "Emotion",
            (
                f"{report.emotion} "
                f"({report.emotion_score})"
            ),
        )

        self._print_section(
            "Strategy",
            report.strategy,
        )
        self._print_section(
            "Product Attribute",
            report.product_attribute,
        )

        self._print_search_plan(
            report
        )

        self._print_section(
            "Prompt",
            (
                report.prompt_summary
                or "-"
            ),
        )

        self._print_section(
            "LLM",
            report.llm_reply,
        )

        self._print_section(
            "LLM Metadata",
            (
                f"Model: {report.llm_model}\n"
                f"Matched Rule: "
                f"{report.matched_rule}"
            ),
        )

        governance_status = (
            "PASS"
            if report.governance_allowed
            else "BLOCKED"
        )

        self._print_section(
            "Governance",
            (
                f"Status: {governance_status}\n"
                f"Risk Score: "
                f"{report.risk_score}\n"
                f"Compliance Score: "
                f"{report.compliance_score}"
            ),
        )

        if report.warnings:
            self._print_section(
                "Warnings",
                "\n".join(
                    f"- {warning}"
                    for warning
                    in report.warnings
                ),
            )

        self._print_section(
            "Final Reply",
            report.final_reply,
        )

        self._print_line("-")
        print(
            "Elapsed: "
            f"{report.execution_time_ms:.2f} ms"
        )
        self._print_line("=")

    def render_scenario_list(
        self,
        scenarios: tuple[Any, ...],
    ) -> None:
        """แสดง Scenario ที่เลือกใช้งานได้."""

        self._print_line("=")
        self._print_center(
            "Available Demo Scenarios"
        )
        self._print_line("=")

        for index, scenario in enumerate(
            scenarios,
            start=1,
        ):
            print(
                f"{index}. "
                f"{scenario.scenario_id}"
            )
            print(
                f"   {scenario.title}"
            )
            print(
                f"   {scenario.customer_message}"
            )

        self._print_line("=")

    def _print_search_plan(
        self,
        report: DemoReport,
    ) -> None:
        """แสดงผล Search Planner."""

        lines: list[str] = [
            (
                "Models: "
                f"{report.extracted_models or []}"
            ),
            (
                "Tokens: "
                f"{report.extracted_tokens or []}"
            ),
            "Top Search Tasks:",
        ]

        if not report.search_tasks:
            lines.append(
                "- ไม่พบ Search Task"
            )

        else:
            for index, task in enumerate(
                report.search_tasks[:5],
                start=1,
            ):
                lines.append(
                    (
                        f"{index}. "
                        f"{task['keyword']} "
                        f"| priority="
                        f"{task['priority']} "
                        f"| score="
                        f"{task['score']} "
                        f"| source="
                        f"{task['source']}"
                    )
                )

        self._print_section(
            "Search Planner",
            "\n".join(
                lines
            ),
        )

    def _print_section(
        self,
        title: str,
        content: str,
    ) -> None:
        """แสดงหัวข้อและเนื้อหา."""

        print()
        print(title)
        self._print_line("-")

        cleaned_content = (
            content.strip()
            if content
            else "-"
        )

        print(
            cleaned_content
        )

    def _print_line(
        self,
        character: str,
    ) -> None:
        """แสดงเส้นแบ่งตามความกว้าง."""

        print(
            character * self.width
        )

    def _print_center(
        self,
        text: str,
    ) -> None:
        """แสดงข้อความกึ่งกลาง."""

        print(
            text.center(
                self.width
            )
        )