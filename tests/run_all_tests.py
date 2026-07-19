"""รัน Unit Test ทั้งหมดของโปรเจกต์."""

from __future__ import annotations

import importlib
import traceback


TEST_MODULES = [
    "tests.test_excel",
    "tests.test_intent",
    "tests.test_knowledge",
    "tests.test_memory",
    "tests.test_nlp",
    "tests.test_product_graph_reader",
    "tests.test_product_intelligence",
    "tests.test_product_search",
    "tests.test_prompt_loader",
    "tests.test_recommendation",
    "tests.test_search_planner",
    "tests.test_voice",

    # Core Architecture
    "tests.test_search_executor",
    "tests.test_prompt_builder",
    "tests.test_answer_builder",
    "tests.test_openai_client",

    # Context and Integration
    "tests.test_context_engine",
    "tests.test_ai_engine",

    "tests.test_sales_brain",
"tests.test_recommendation_search",
]


def run_test_module(
    module_name: str,
) -> bool:
    """Import และรัน main() ของ Test Module."""

    test_name = module_name.split(".")[-1]

    try:
        module = importlib.import_module(
            module_name
        )

        test_main = getattr(
            module,
            "main",
            None,
        )

        if not callable(test_main):
            raise AttributeError(
                f"{module_name} ไม่มีฟังก์ชัน main()"
            )

        test_main()

        print(
            f"✓ {test_name}"
        )

        return True

    except Exception:
        print(
            f"✗ {test_name}"
        )

        traceback.print_exc()

        return False


def main() -> None:
    """รัน Test Suite และแสดงผลรวม."""

    print("=" * 60)
    print("Running AI Live Streamer Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    for module_name in TEST_MODULES:
        if run_test_module(
            module_name
        ):
            passed += 1
        else:
            failed += 1

    total = passed + failed

    print("=" * 60)
    print(
        f"Total  : {total}"
    )
    print(
        f"Passed : {passed}"
    )
    print(
        f"Failed : {failed}"
    )
    print("=" * 60)

    if failed == 0:
        print(
            "🎉 All tests passed"
        )
        return

    raise SystemExit(
        1
    )


if __name__ == "__main__":
    main()