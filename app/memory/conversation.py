"""Conversation memory สำหรับ AI Commerce OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """ข้อความหนึ่งรอบในบทสนทนา."""

    role: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized_role = self.role.strip().lower()

        if normalized_role not in {"customer", "assistant", "system"}:
            raise ValueError(f"ไม่รองรับ role: {self.role!r}")

        if not self.text.strip():
            raise ValueError("ConversationTurn.text ต้องไม่ว่าง")

        object.__setattr__(self, "role", normalized_role)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ConversationMemory:
    """หน่วยความจำระยะสั้นของบทสนทนา."""

    max_turns: int = 12
    turns: list[ConversationTurn] = field(default_factory=list)
    active_models: list[str] = field(default_factory=list)

    current_topic: str | None = None
    current_intent: str | None = None

    def __post_init__(self) -> None:
        if self.max_turns <= 0:
            raise ValueError("max_turns ต้องมากกว่า 0")

    def add_turn(
        self,
        *,
        role: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        turn = ConversationTurn(
            role=role,
            text=text,
            metadata=metadata or {},
        )
        self.turns.append(turn)

        if len(self.turns) > self.max_turns:
            del self.turns[: len(self.turns) - self.max_turns]

        self._update_active_models(turn)
        return turn

    def add_customer(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        return self.add_turn(
            role="customer",
            text=text,
            metadata=metadata,
        )

    def add_assistant(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        return self.add_turn(
            role="assistant",
            text=text,
            metadata=metadata,
        )

    def clear(self) -> None:
        self.turns.clear()
        self.active_models.clear()
        self.current_topic = None
        self.current_intent = None

    def recent_turns(
        self,
        *,
        limit: int = 6,
    ) -> list[ConversationTurn]:
        normalized_limit = max(int(limit), 0)

        if normalized_limit == 0:
            return []

        return list(self.turns[-normalized_limit:])

    def latest_customer_message(self) -> str:
        for turn in reversed(self.turns):
            if turn.role == "customer":
                return turn.text

        return ""

    def latest_assistant_message(self) -> str:
        for turn in reversed(self.turns):
            if turn.role == "assistant":
                return turn.text

        return ""

    def resolve_models(
        self,
        extracted_models: list[str],
    ) -> list[str]:
        normalized = self._normalize_models(extracted_models)

        if normalized:
            self.active_models = normalized
            return list(normalized)

        return list(self.active_models)

    def update_context(
        self,
        *,
        topic: str | None = None,
        intent: str | None = None,
    ) -> None:
        """อัปเดตสถานะการสนทนาปัจจุบัน."""

        if topic is not None:
            self.current_topic = topic

        if intent is not None:
            self.current_intent = intent

    def build_context_text(
        self,
        *,
        limit: int = 6,
    ) -> str:
        recent = self.recent_turns(limit=limit)

        if not recent:
            return "ยังไม่มีประวัติการสนทนาก่อนหน้า"

        role_labels = {
            "customer": "ลูกค้า",
            "assistant": "ผู้ช่วย",
            "system": "ระบบ",
        }

        summary = []

        if self.current_topic:
         summary.append(f"หัวข้อปัจจุบัน: {self.current_topic}")

        if self.current_intent:
         summary.append(f"เจตนาปัจจุบัน: {self.current_intent}")

        if self.active_models:
         summary.append(
        "สินค้าปัจจุบัน: "
        + ", ".join(self.active_models)
    )

        lines = [
    f"{role_labels[turn.role]}: {turn.text}"
    for turn in recent
]

        if summary:
         return "\n".join(summary) + "\n\n" + "\n".join(lines)

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_turns": self.max_turns,
            "turns": [turn.to_dict() for turn in self.turns],
            "active_models": list(self.active_models),
        }

    def _update_active_models(
        self,
        turn: ConversationTurn,
    ) -> None:
        raw_models = turn.metadata.get("models", [])

        if not isinstance(raw_models, list):
            return

        normalized = self._normalize_models(
            [str(model) for model in raw_models]
        )

        if normalized:
            self.active_models = normalized

    @staticmethod
    def _normalize_models(
        models: list[str],
    ) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for model in models:
            cleaned = model.strip()

            if not cleaned:
                continue

            key = cleaned.lower()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(cleaned)

        return normalized
