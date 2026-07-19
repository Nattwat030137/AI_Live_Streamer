"""Shared pytest fixtures for the AI Live Streamer test suite."""

from __future__ import annotations

import pytest

from app.llm.config import LLMConfig
from demo.bakery_demo import BakeryDemo


@pytest.fixture
def demo(request) -> BakeryDemo:
    """Create the correct BakeryDemo instance for each integration-test module."""

    module_name = request.module.__name__

    if module_name.endswith("test_bakery_demo_openai_dry_run"):
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

    return BakeryDemo()
