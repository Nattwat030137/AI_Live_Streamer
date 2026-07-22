"""Tests for production runtime configuration."""

from pathlib import Path

from app.runtime_config import inspect_runtime_config


def test_mock_runtime_is_ready(
    tmp_path: Path,
) -> None:
    product_database = (
        tmp_path / "products.db"
    )
    product_database.write_bytes(b"sqlite")
    audio_directory = tmp_path / "audio"
    audio_directory.mkdir()

    status = inspect_runtime_config(
        provider_name="mock",
        voice_enabled=False,
        api_key="",
        product_database=product_database,
        audio_directory=audio_directory,
    )

    assert status.ready is True
    assert status.provider_name == "mock"
    assert status.errors == ()


def test_openai_requires_api_key(
    tmp_path: Path,
) -> None:
    product_database = (
        tmp_path / "products.db"
    )
    product_database.write_bytes(b"sqlite")
    audio_directory = tmp_path / "audio"
    audio_directory.mkdir()

    status = inspect_runtime_config(
        provider_name="openai",
        voice_enabled=True,
        api_key="",
        product_database=product_database,
        audio_directory=audio_directory,
    )

    assert status.ready is False
    assert "OPENAI_API_KEY is required" in status.errors


def test_missing_product_database_is_reported(
    tmp_path: Path,
) -> None:
    status = inspect_runtime_config(
        provider_name="mock",
        voice_enabled=False,
        api_key="",
        product_database=(
            tmp_path / "missing.db"
        ),
        audio_directory=tmp_path / "audio",
    )

    assert status.ready is False
    assert (
        "Product database is missing"
        in status.errors
    )