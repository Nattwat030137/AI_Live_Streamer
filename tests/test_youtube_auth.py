"""Tests for YouTube OAuth authorization."""

from pathlib import Path

import pytest

from app.youtube_auth import build_youtube_service


def test_missing_oauth_client_file_is_rejected(
    tmp_path: Path,
) -> None:
    """Reject a missing OAuth client configuration."""

    missing_client_file = (
        tmp_path
        / "missing-client.json"
    )
    token_file = (
        tmp_path
        / "youtube-token.json"
    )

    with pytest.raises(
        FileNotFoundError,
        match=(
            "YouTube OAuth client file "
            "was not found"
        ),
    ):
        build_youtube_service(
            client_file=missing_client_file,
            token_file=token_file,
        )