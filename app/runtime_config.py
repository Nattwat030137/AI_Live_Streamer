"""Production runtime configuration inspection."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.llm.factory import LLMFactory
from config.settings import (
    OPENAI_API_KEY,
    PROJECT_ROOT,
)


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Serializable readiness status for the application."""

    provider_name: str
    voice_enabled: bool
    api_key_configured: bool
    product_database_exists: bool
    audio_directory_exists: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        """Return whether the application can start safely."""

        return not self.errors


def _resolve_boolean(
    value: str,
) -> bool:
    """Resolve a common environment boolean value."""

    return value.strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def inspect_runtime_config(
    *,
    provider_name: str | None = None,
    voice_enabled: bool | None = None,
    api_key: str | None = None,
    product_database: Path | None = None,
    audio_directory: Path | None = None,
) -> RuntimeStatus:
    """Inspect runtime dependencies without calling external APIs."""

    resolved_provider = (
        LLMFactory.resolve_provider_name(
            provider_name
        )
    )
    resolved_voice = (
        voice_enabled
        if voice_enabled is not None
        else _resolve_boolean(
            os.getenv(
                "VOICE_ENABLED",
                "true",
            )
        )
    )

    resolved_api_key = (
        api_key
        if api_key is not None
        else os.getenv(
            "OPENAI_API_KEY",
            OPENAI_API_KEY,
        )
    ).strip()

    database_path = (
        product_database
        if product_database is not None
        else PROJECT_ROOT / "data" / "products.db"
    )
    audio_path = (
        audio_directory
        if audio_directory is not None
        else PROJECT_ROOT / "audio"
    )

    errors: list[str] = []
    warnings: list[str] = []

    if not LLMFactory.is_supported(
        resolved_provider
    ):
        errors.append(
            "Unsupported LLM provider: "
            f"{resolved_provider}"
        )

    if (
        resolved_provider == "openai"
        or resolved_voice
    ) and not resolved_api_key:
        errors.append(
            "OPENAI_API_KEY is required"
        )

    database_exists = (
        database_path.is_file()
        and database_path.stat().st_size > 0
    )

    if not database_exists:
        errors.append(
            "Product database is missing"
        )

    audio_exists = audio_path.is_dir()

    if resolved_voice and not audio_exists:
        warnings.append(
            "Audio directory will be created"
        )

    return RuntimeStatus(
        provider_name=resolved_provider,
        voice_enabled=resolved_voice,
        api_key_configured=bool(
            resolved_api_key
        ),
        product_database_exists=(
            database_exists
        ),
        audio_directory_exists=audio_exists,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )