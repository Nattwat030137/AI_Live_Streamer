"""OAuth authorization for the YouTube Data API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


YOUTUBE_SCOPES = (
    "https://www.googleapis.com/auth/"
    "youtube.force-ssl",
)

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


def _resolve_external_path(
    path: str | Path,
    *,
    label: str,
) -> Path:
    """Resolve a secret path and reject repository locations."""

    resolved_path = Path(
        path
    ).expanduser().resolve()

    if resolved_path.is_relative_to(
        PROJECT_ROOT
    ):
        raise ValueError(
            f"{label} must be stored "
            "outside the repository"
        )

    return resolved_path


def build_youtube_service(
    *,
    client_file: str | Path,
    token_file: str | Path,
) -> Any:
    """Authorize and build a YouTube Data API client."""

    resolved_client_file = (
        _resolve_external_path(
            client_file,
            label=(
                "YouTube OAuth client file"
            ),
        )
    )
    resolved_token_file = (
        _resolve_external_path(
            token_file,
            label=(
                "YouTube OAuth token file"
            ),
        )
    )

    if not resolved_client_file.is_file():
        raise FileNotFoundError(
            "YouTube OAuth client file "
            "was not found"
        )

    credentials: Credentials | None = None

    if resolved_token_file.is_file():
        credentials = (
            Credentials
            .from_authorized_user_file(
                str(resolved_token_file),
                scopes=list(
                    YOUTUBE_SCOPES
                ),
            )
        )

    if (
        credentials is None
        or not credentials.valid
    ):
        if (
            credentials is not None
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(
                Request()
            )
        else:
            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    str(
                        resolved_client_file
                    ),
                    scopes=list(
                        YOUTUBE_SCOPES
                    ),
                )
            )
            credentials = (
                flow.run_local_server(
                    port=0,
                    open_browser=True,
                )
            )

        resolved_token_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        resolved_token_file.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )