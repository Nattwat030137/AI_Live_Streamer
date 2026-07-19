"""
AI Commerce OS

Module:
    Policy Registry

Responsibility:
    ลงทะเบียน ค้นหา จัดลำดับ และจัดการ Policy Plugins

Design Patterns:
    Registry Pattern
    Dependency Inversion
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.policies.base import BasePolicy


class PolicyRegistry:
    """
    Registry กลางสำหรับจัดการ Policy Plugins.

    Registry ไม่รู้รายละเอียดของ Business, Shopee, Lazada
    หรือแพลตฟอร์มใดโดยตรง แต่จัดการทุก Policy ผ่าน BasePolicy
    ซึ่งเป็น Interface กลางของ Governance Runtime
    """

    def __init__(
        self,
        policies: Iterable[BasePolicy] | None = None,
    ) -> None:
        """สร้าง Registry และลงทะเบียน Policy เริ่มต้น."""

        self._policies: dict[
            str,
            BasePolicy,
        ] = {}

        if policies is not None:
            self.register_many(
                policies
            )

    @staticmethod
    def normalize_name(
        name: str,
    ) -> str:
        """ปรับชื่อ Policy สำหรับใช้เป็น Registry Key."""

        return name.strip().lower()

    @property
    def count(self) -> int:
        """คืนจำนวน Policy ทั้งหมด."""

        return len(
            self._policies
        )

    @property
    def names(self) -> tuple[str, ...]:
        """คืนชื่อ Policy ทั้งหมดตามลำดับลงทะเบียน."""

        return tuple(
            policy.name
            for policy in self._policies.values()
        )

    @property
    def policies(self) -> tuple[BasePolicy, ...]:
        """คืน Policy ทั้งหมดตามลำดับลงทะเบียน."""

        return tuple(
            self._policies.values()
        )

    @property
    def enabled_policies(
        self,
    ) -> tuple[BasePolicy, ...]:
        """คืน Policy ที่เปิดใช้งาน."""

        return tuple(
            policy
            for policy in self._policies.values()
            if policy.enabled
        )

    @property
    def disabled_policies(
        self,
    ) -> tuple[BasePolicy, ...]:
        """คืน Policy ที่ปิดใช้งาน."""

        return tuple(
            policy
            for policy in self._policies.values()
            if not policy.enabled
        )

    def __len__(self) -> int:
        """รองรับ len(registry)."""

        return self.count

    def __contains__(
        self,
        name: object,
    ) -> bool:
        """รองรับการตรวจชื่อ Policy ด้วย in."""

        if not isinstance(
            name,
            str,
        ):
            return False

        return self.contains(
            name
        )

    def __iter__(self):
        """วนซ้ำ Policy ตามลำดับลงทะเบียน."""

        return iter(
            self._policies.values()
        )

    def register(
        self,
        policy: BasePolicy,
        *,
        replace: bool = False,
    ) -> BasePolicy:
        """
        ลงทะเบียน Policy หนึ่งตัว.

        Args:
            policy:
                Policy Plugin ที่ต้องการลงทะเบียน
            replace:
                อนุญาตให้แทนที่ Policy ชื่อเดิมหรือไม่
        """

        if not isinstance(
            policy,
            BasePolicy,
        ):
            raise TypeError(
                "policy ต้องเป็น BasePolicy"
            )

        normalized_name = (
            self.normalize_name(
                policy.name
            )
        )

        if not normalized_name:
            raise ValueError(
                "ชื่อ Policy ต้องไม่ว่าง"
            )

        if (
            normalized_name
            in self._policies
            and not replace
        ):
            raise ValueError(
                "Policy ถูกลงทะเบียนแล้ว: "
                f"{policy.name}"
            )

        self._policies[
            normalized_name
        ] = policy

        return policy

    def register_many(
        self,
        policies: Iterable[BasePolicy],
        *,
        replace: bool = False,
    ) -> tuple[BasePolicy, ...]:
        """
        ลงทะเบียน Policy หลายตัว.

        หากรายการใดผิดพลาด Policy ก่อนหน้าที่ลงทะเบียนสำเร็จ
        จะยังคงอยู่ใน Registry
        """

        registered: list[
            BasePolicy
        ] = []

        for policy in policies:
            registered_policy = self.register(
                policy,
                replace=replace,
            )

            registered.append(
                registered_policy
            )

        return tuple(
            registered
        )

    def contains(
        self,
        name: str,
    ) -> bool:
        """ตรวจว่ามี Policy ชื่อนี้หรือไม่."""

        normalized_name = (
            self.normalize_name(
                name
            )
        )

        if not normalized_name:
            return False

        return (
            normalized_name
            in self._policies
        )

    def get(
        self,
        name: str,
    ) -> BasePolicy | None:
        """ค้น Policy จากชื่อ หากไม่พบคืน None."""

        normalized_name = (
            self.normalize_name(
                name
            )
        )

        if not normalized_name:
            return None

        return self._policies.get(
            normalized_name
        )

    def require(
        self,
        name: str,
    ) -> BasePolicy:
        """
        ค้น Policy จากชื่อ.

        Raises:
            KeyError:
                เมื่อไม่พบ Policy
        """

        policy = self.get(
            name
        )

        if policy is None:
            raise KeyError(
                "ไม่พบ Policy: "
                f"{name}"
            )

        return policy

    def unregister(
        self,
        name: str,
    ) -> BasePolicy | None:
        """ลบ Policy จาก Registry และคืนตัวที่ถูกลบ."""

        normalized_name = (
            self.normalize_name(
                name
            )
        )

        if not normalized_name:
            return None

        return self._policies.pop(
            normalized_name,
            None,
        )

    def clear(self) -> None:
        """ลบ Policy ทั้งหมดออกจาก Registry."""

        self._policies.clear()

    def replace(
        self,
        policy: BasePolicy,
    ) -> BasePolicy:
        """แทนที่ Policy ชื่อเดิมหรือเพิ่มใหม่ถ้ายังไม่มี."""

        return self.register(
            policy,
            replace=True,
        )

    def get_by_metadata(
        self,
        key: str,
        value: Any,
    ) -> tuple[BasePolicy, ...]:
        """ค้น Policy จาก Metadata Key และ Value."""

        cleaned_key = key.strip()

        if not cleaned_key:
            return ()

        matched_policies = [
            policy
            for policy in self._policies.values()
            if policy.metadata.get(
                cleaned_key
            ) == value
        ]

        return tuple(
            matched_policies
        )

    def get_by_platform(
        self,
        platform: str,
    ) -> tuple[BasePolicy, ...]:
        """
        ค้น Policy ที่ระบุ Platform ใน Metadata.

        Policy กลางที่มี platform เป็น generic หรือ all
        จะถูกรวมด้วย
        """

        normalized_platform = (
            platform.strip().lower()
        )

        if not normalized_platform:
            normalized_platform = "generic"

        matched_policies: list[
            BasePolicy
        ] = []

        for policy in self._policies.values():
            metadata = policy.metadata

            policy_platform = str(
                metadata.get(
                    "platform",
                    "generic",
                )
            ).strip().lower()

            if policy_platform in {
                "generic",
                "all",
                "*",
                normalized_platform,
            }:
                matched_policies.append(
                    policy
                )

        return tuple(
            matched_policies
        )

    def execution_order(
        self,
        *,
        platform: str | None = None,
        enabled_only: bool = True,
    ) -> tuple[BasePolicy, ...]:
        """
        คืน Policy ตามลำดับการทำงาน.

        ลำดับอิงจาก Metadata ชื่อ priority โดยค่ามากทำงานก่อน
        หาก Priority เท่ากันจะรักษาลำดับลงทะเบียนเดิม
        """

        if platform is None:
            candidates = list(
                self._policies.values()
            )

        else:
            candidates = list(
                self.get_by_platform(
                    platform
                )
            )

        if enabled_only:
            candidates = [
                policy
                for policy in candidates
                if policy.enabled
            ]

        indexed_policies = list(
            enumerate(
                candidates
            )
        )

        indexed_policies.sort(
            key=lambda item: (
                -self._get_priority(
                    item[1]
                ),
                item[0],
            )
        )

        return tuple(
            policy
            for _,
            policy in indexed_policies
        )

    @staticmethod
    def _get_priority(
        policy: BasePolicy,
    ) -> int:
        """อ่าน Priority จาก Metadata อย่างปลอดภัย."""

        raw_priority = policy.metadata.get(
            "priority",
            50,
        )

        try:
            return int(
                raw_priority
            )

        except (
            TypeError,
            ValueError,
        ):
            return 50

    def to_dict(self) -> dict[str, Any]:
        """แปลง Registry เป็น Dictionary."""

        return {
            "count": self.count,
            "names": list(
                self.names
            ),
            "enabled_count": len(
                self.enabled_policies
            ),
            "disabled_count": len(
                self.disabled_policies
            ),
            "policies": [
                policy.to_dict()
                for policy in self._policies.values()
            ],
        }


_default_registry = PolicyRegistry()


def get_default_registry() -> PolicyRegistry:
    """คืน Global Registry เริ่มต้น."""

    return _default_registry


def register_policy(
    policy: BasePolicy,
    *,
    replace: bool = False,
) -> BasePolicy:
    """ลงทะเบียน Policy เข้า Global Registry."""

    return _default_registry.register(
        policy,
        replace=replace,
    )


def unregister_policy(
    name: str,
) -> BasePolicy | None:
    """ลบ Policy จาก Global Registry."""

    return _default_registry.unregister(
        name
    )


def clear_default_registry() -> None:
    """ล้าง Policy ทั้งหมดจาก Global Registry."""

    _default_registry.clear()