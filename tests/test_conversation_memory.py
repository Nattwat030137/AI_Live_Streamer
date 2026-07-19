"""Regression tests สำหรับ ConversationMemory."""

from app.memory.conversation import (
    ConversationMemory,
    ConversationTurn,
)


def main() -> None:
    print("=" * 60)
    print("Conversation Memory Regression Test")
    print("=" * 60)

    passed = 0
    total = 9

    turn = ConversationTurn(
        role="customer",
        text="รุ่น5040คืออะไร",
    )
    assert turn.role == "customer"
    assert turn.text == "รุ่น5040คืออะไร"
    passed += 1
    print("Create turn........................PASS")

    memory = ConversationMemory(max_turns=3)

    memory.add_customer(
        "รุ่น5040คืออะไร",
        metadata={"models": ["5040"]},
    )
    assert memory.active_models == ["5040"]
    passed += 1
    print("Remember model.....................PASS")

    assert memory.resolve_models([]) == ["5040"]
    passed += 1
    print("Resolve missing model..............PASS")

    assert memory.resolve_models(["5073", "5073"]) == ["5073"]
    assert memory.active_models == ["5073"]
    passed += 1
    print("Replace active model...............PASS")

    memory.add_assistant("รุ่น 5073 เป็นถาดเบเกอรี่ค่ะ")
    memory.add_customer("แล้วใช้ถุงอะไร")
    memory.add_assistant("ใช้ถุง 12 x 20 ซม. ค่ะ")

    assert len(memory.turns) == 3
    assert memory.turns[0].role == "assistant"
    passed += 1
    print("Trim old turns.....................PASS")

    context = memory.build_context_text()
    assert "ผู้ช่วย:" in context
    assert "ลูกค้า: แล้วใช้ถุงอะไร" in context
    passed += 1
    print("Build context......................PASS")

    assert memory.latest_customer_message() == "แล้วใช้ถุงอะไร"
    assert memory.latest_assistant_message() == "ใช้ถุง 12 x 20 ซม. ค่ะ"
    passed += 1
    print("Latest messages....................PASS")

    memory.clear()
    assert memory.turns == []
    assert memory.active_models == []
    assert memory.current_topic is None
    assert memory.current_intent is None
    passed += 1
    print("Clear memory.......................PASS")

    memory.update_context(
    topic="PRICE_REQUEST",
    intent="information",
    )
    assert memory.current_topic == "PRICE_REQUEST"
    assert memory.current_intent == "information"
    passed += 1
    print("Update context.....................PASS")

    print("=" * 60)
    print(f"{passed} / {total} PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
