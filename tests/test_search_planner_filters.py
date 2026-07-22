"""Regression tests for Search Planner filter extraction."""

from app.search_planner import create_search_plan


def _task_keywords(plan):
    return [task.keyword for task in plan.tasks]


def test_detect_single_model():
    plan = create_search_plan("รุ่น 5040")

    assert "5040" in plan.extracted_models


def test_detect_multiple_models():
    plan = create_search_plan("5040 กับ 5073")

    assert "5040" in plan.extracted_models
    assert "5073" in plan.extracted_models


def test_cupcake_query_creates_tasks():
    plan = create_search_plan("ถ้วยคัพเค้กสีน้ำตาล")

    keywords = _task_keywords(plan)

    assert any("คัพ" in k or "cup" in k.lower() for k in keywords)


def test_bag_query_keeps_model():
    plan = create_search_plan("ถุง OPP สำหรับ 5040")

    assert "5040" in plan.extracted_models

    keywords = _task_keywords(plan)

    assert any("opp" in k.lower() for k in keywords)


def test_material_keyword():
    plan = create_search_plan("วัสดุกระดาษ")

    keywords = _task_keywords(plan)

    assert any("กระดาษ" in k for k in keywords)


def test_tasks_are_sorted():
    plan = create_search_plan(
        "ถุง OPP สำหรับ 5040",
    )

    priorities = [
        task.priority
        for task in plan.tasks
    ]

    assert priorities == sorted(
        priorities,
        reverse=True,
    )
