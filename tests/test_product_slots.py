"""Regression tests for ProductSlots."""

from __future__ import annotations

from app.memory.product_slots import ProductSlots


def print_result(
    name: str,
    passed: bool,
) -> None:
    """แสดงผลการทดสอบหนึ่งรายการ."""

    status = "PASS" if passed else "FAIL"

    print(
        f"{name:.<35}{status}"
    )


def run_tests() -> None:
    """รัน ProductSlots regression tests."""

    print("=" * 60)
    print("Product Slot Memory Regression Test")
    print("=" * 60)

    results: list[bool] = []

    slots = ProductSlots()

    passed = not slots.has_product()
    results.append(passed)
    print_result(
        "Create empty slots",
        passed,
    )

    slots.update(
        model="5073",
        name="ถาดเบเกอรี่ รุ่น 5073",
        category="ถาดเบเกอรี่",
        material="PET",
        color="ใส",
        bag_size="12 x 20 ซม.",
    )

    passed = slots.has_product()
    results.append(passed)
    print_result(
        "Remember active product",
        passed,
    )

    passed = slots.get("model") == "5073"
    results.append(passed)
    print_result(
        "Read model slot",
        passed,
    )

    passed = slots.get("color") == "ใส"
    results.append(passed)
    print_result(
        "Read color slot",
        passed,
    )

    slots.update(
        color="ดำ",
    )

    passed = (
        slots.model == "5073"
        and slots.color == "ดำ"
    )
    results.append(passed)
    print_result(
        "Update one slot",
        passed,
    )

    slots.update(
        extra={
            "stock_status": "unknown",
        }
    )

    passed = (
        slots.get("stock_status")
        == "unknown"
    )
    results.append(passed)
    print_result(
        "Remember extra slot",
        passed,
    )

    context_text = (
        slots.build_context_text()
    )

    passed = (
        "รหัสสินค้า: 5073"
        in context_text
        and "วัสดุ: PET"
        in context_text
        and "สี: ดำ"
        in context_text
    )
    results.append(passed)
    print_result(
        "Build slot context",
        passed,
    )

    slot_data = slots.to_dict()

    passed = (
        slot_data["model"] == "5073"
        and slot_data["material"] == "PET"
    )
    results.append(passed)
    print_result(
        "Convert slots to dict",
        passed,
    )

    slots.clear()

    passed = (
        not slots.has_product()
        and slots.color is None
        and slots.extra == {}
    )
    results.append(passed)
    print_result(
        "Clear product slots",
        passed,
    )

    passed_count = sum(results)
    total_count = len(results)

    print("=" * 60)
    print(
        f"{passed_count} / "
        f"{total_count} PASSED"
    )
    print("=" * 60)

    if passed_count != total_count:
        raise SystemExit(1)


if __name__ == "__main__":
    run_tests()