"""ทดสอบระบบ Conversation Memory."""

from app.conversation_memory import ConversationMemory


def main() -> None:

    memory = ConversationMemory(
        max_messages=4,
    )

    memory.add_user_message(
        "มีถ้วยคัพเค้กไหม"
    )

    memory.add_assistant_message(
        "มีค่ะ มีหลายแบบค่ะ"
    )

    memory.add_user_message(
        "แบบแรกมีขนาดเท่าไร"
    )

    memory.add_assistant_message(
        "ขออนุญาตตรวจสอบรายละเอียดให้ค่ะ"
    )

    print("=" * 60)

    print("ข้อความใน Memory")

    print("=" * 60)

    for message in memory.get_messages():

        print(
            f"{message['role']} : {message['content']}"
        )

    print("=" * 60)

    print(
        "จำนวนข้อความ:",
        len(memory),
    )


if __name__ == "__main__":
    main()