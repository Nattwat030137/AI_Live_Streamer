"""Integration tests สำหรับ BakeryDemo + OpenAI dry-run."""

from __future__ import annotations

import pytest

from app.llm.config import LLMConfig

from app.llm.config import LLMConfig
from demo.bakery_demo import BakeryDemo
from demo.sample_data import DemoScenario


def build_demo() -> BakeryDemo:
    """สร้าง BakeryDemo ที่ใช้ OpenAI dry-run."""

    config = LLMConfig(
        provider="openai",
        openai_api_key="test-key",
        openai_model="gpt-5-mini",
        openai_timeout_seconds=30.0,
        openai_max_output_tokens=500,
    )

    return BakeryDemo(
        provider_name="openai",
        provider_options={
            "config": config,
            "dry_run": True,
        },
    )


def assert_common_report(report) -> None:
    """ตรวจค่าพื้นฐานของรายงาน."""

    assert report.llm_model == "gpt-5-mini"
    assert report.llm_reply.strip()
    assert report.final_reply.strip()
    assert report.governance_allowed is True
    assert report.risk_score == 0
    assert report.compliance_score == 100
    assert report.execution_time_ms >= 0


def test_health_check(demo: BakeryDemo) -> None:
    """ทดสอบ Health Check ของ OpenAI dry-run."""

    health = demo.llm.health_check()

    assert health.healthy is True
    assert health.provider == "openai"
    assert health.metadata["dry_run"] is True
    assert health.metadata["model"] == "gpt-5-mini"


def test_greeting_pipeline(demo: BakeryDemo) -> None:
    """ทดสอบ Pipeline ด้วย Greeting."""

    scenario = DemoScenario(
        scenario_id="openai-dry-run-greeting",
        title="OpenAI Dry Run Greeting",
        customer_message="สวัสดีครับ",
        platform="shopee",
        expected_rule="",
    )

    report = demo.run_scenario(scenario)
    assert_common_report(report)

    assert report.llm_reply == (
        "[DRY RUN] OpenAI request validated successfully."
    )
    assert report.matched_rule == ""


def test_product_pipeline(demo: BakeryDemo) -> None:
    """ทดสอบ Pipeline ด้วยคำถามสินค้า."""

    scenario = DemoScenario(
        scenario_id="openai-dry-run-product",
        title="OpenAI Dry Run Product",
        customer_message="รุ่น5040",
        platform="shopee",
        expected_rule="",
    )

    report = demo.run_scenario(scenario)
    assert_common_report(report)

    search_plan = report.metadata["search_plan"]
    assert "5040" in search_plan["extracted_models"]
    assert report.llm_reply == (
        "[DRY RUN] OpenAI request validated successfully."
    )


def test_provider_metadata(demo: BakeryDemo) -> None:
    """ทดสอบ Metadata ของ Provider."""

    metadata = demo.llm.metadata()

    assert metadata["provider"] == "openai"
    assert metadata["default_model"] == "gpt-5-mini"
    assert metadata["dry_run"] is True
    assert metadata["supports_streaming"] is False


def main() -> None:
    """รัน Integration Test ของ OpenAI dry-run."""

    demo = build_demo()

    tests = (
        ("Health Check", test_health_check),
        ("Greeting Pipeline", test_greeting_pipeline),
        ("Product Pipeline", test_product_pipeline),
        ("Provider Metadata", test_provider_metadata),
    )

    passed = 0

    print("=" * 60)
    print("BakeryDemo OpenAI Dry-Run Integration Test")
    print("=" * 60)

    for name, test_function in tests:
        test_function(demo)
        passed += 1
        print(f"{name:.<38}PASS")

    print("=" * 60)
    print(f"{passed} / {len(tests)} PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
