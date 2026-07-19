"""Product slot memory for active products."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductSlots:
    """เก็บข้อมูลสำคัญของสินค้าที่กำลังสนทนา."""

    model: str | None = None
    name: str | None = None
    category: str | None = None
    material: str | None = None
    color: str | None = None
    bag_size: str | None = None
    notes: str | None = None
    extra: dict[str, Any] = field(
        default_factory=dict
    )

    def update(
        self,
        *,
        model: str | None = None,
        name: str | None = None,
        category: str | None = None,
        material: str | None = None,
        color: str | None = None,
        bag_size: str | None = None,
        notes: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """อัปเดตเฉพาะค่าที่ถูกส่งเข้ามา."""

        values = {
            "model": model,
            "name": name,
            "category": category,
            "material": material,
            "color": color,
            "bag_size": bag_size,
            "notes": notes,
        }

        for field_name, value in values.items():
            if value is not None:
                setattr(
                    self,
                    field_name,
                    str(value).strip(),
                )

        if extra:
            self.extra.update(extra)

    def clear(self) -> None:
        """ล้างข้อมูลสินค้าเดิมทั้งหมด."""

        self.model = None
        self.name = None
        self.category = None
        self.material = None
        self.color = None
        self.bag_size = None
        self.notes = None
        self.extra.clear()

    def get(self, slot_name: str) -> Any:
        """อ่านค่า Slot ตามชื่อ."""

        normalized_name = (
            str(slot_name)
            .strip()
            .lower()
        )

        if hasattr(self, normalized_name):
            return getattr(
                self,
                normalized_name,
            )

        return self.extra.get(
            normalized_name
        )

    def has_product(self) -> bool:
        """ตรวจว่ามีสินค้าปัจจุบันหรือไม่."""

        return bool(self.model)

    def to_dict(self) -> dict[str, Any]:
        """แปลง Slot ทั้งหมดเป็น Dictionary."""

        return {
            "model": self.model,
            "name": self.name,
            "category": self.category,
            "material": self.material,
            "color": self.color,
            "bag_size": self.bag_size,
            "notes": self.notes,
            "extra": dict(self.extra),
        }

    def build_context_text(self) -> str:
        """สร้างข้อความสรุปสำหรับใส่ใน Prompt."""

        slot_labels = (
            ("model", "รหัสสินค้า"),
            ("name", "ชื่อสินค้า"),
            ("category", "หมวดสินค้า"),
            ("material", "วัสดุ"),
            ("color", "สี"),
            ("bag_size", "ขนาดถุง"),
            ("notes", "หมายเหตุ"),
        )

        lines: list[str] = []

        for slot_name, label in slot_labels:
            value = getattr(
                self,
                slot_name,
            )

            if value:
                lines.append(
                    f"{label}: {value}"
                )

        for key, value in self.extra.items():
            if value is not None:
                lines.append(
                    f"{key}: {value}"
                )

        return "\n".join(lines)