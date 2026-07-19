"""Pytest coverage for Sprint 28 conversation memory."""

from app.memory.conversation import (
    ConversationMemory,
    ConversationTurn,
)
from app.memory.product_slots import ProductSlots
from app.memory.reference_resolver import resolve_reference


def test_create_conversation_turn() -> None:
    turn = ConversationTurn(
        role="CUSTOMER",
        text="รุ่น 5040 คืออะไร",
    )

    assert turn.role == "customer"
    assert turn.text == "รุ่น 5040 คืออะไร"


def test_remember_and_resolve_active_model() -> None:
    memory = ConversationMemory()

    memory.add_customer(
        "มีรุ่น 5040 ไหม",
        metadata={"models": ["5040"]},
    )

    assert memory.active_models == ["5040"]
    assert memory.resolve_models([]) == ["5040"]


def test_new_model_replaces_previous_model() -> None:
    memory = ConversationMemory()

    assert memory.resolve_models(["5040"]) == ["5040"]
    assert memory.resolve_models(["5073", "5073"]) == ["5073"]
    assert memory.active_models == ["5073"]


def test_follow_up_reference_uses_active_model() -> None:
    memory = ConversationMemory()
    memory.active_models = ["5040"]

    assert resolve_reference(
        "มีสีอะไร",
        memory,
    ) == "5040"

    assert resolve_reference(
        "ใช้ถุงอะไร",
        memory,
    ) == "5040"

    assert resolve_reference(
        "วัสดุอะไร",
        memory,
    ) == "5040"


def test_explicit_model_does_not_use_old_reference() -> None:
    memory = ConversationMemory()
    memory.active_models = ["5040"]

    assert resolve_reference(
        "แล้วรุ่น 5073 ล่ะ",
        memory,
    ) is None


def test_memory_trims_old_turns() -> None:
    memory = ConversationMemory(max_turns=3)

    memory.add_customer("ข้อความ 1")
    memory.add_assistant("ข้อความ 2")
    memory.add_customer("ข้อความ 3")
    memory.add_assistant("ข้อความ 4")

    assert len(memory.turns) == 3
    assert memory.turns[0].text == "ข้อความ 2"
    assert memory.turns[-1].text == "ข้อความ 4"


def test_product_slots_store_product_context() -> None:
    slots = ProductSlots()

    slots.update(
        model="5040",
        name="ถ้วยคัพเค้ก",
        material="กระดาษ",
        color="น้ำตาล",
        bag_size="12 x 20 ซม.",
    )

    assert slots.has_product()
    assert slots.get("model") == "5040"
    assert slots.get("material") == "กระดาษ"
    assert slots.get("bag_size") == "12 x 20 ซม."

    context = slots.build_context_text()

    assert "5040" in context
    assert "กระดาษ" in context
    assert "12 x 20 ซม." in context


def test_clear_resets_all_conversation_state() -> None:
    memory = ConversationMemory()

    memory.add_customer(
        "รุ่น 5040",
        metadata={"models": ["5040"]},
    )
    memory.update_context(
        topic="product",
        intent="information",
    )

    memory.clear()

    assert memory.turns == []
    assert memory.active_models == []
    assert memory.current_topic is None
    assert memory.current_intent is None
