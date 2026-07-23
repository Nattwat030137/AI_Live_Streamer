"""Read YouTube Live Chat safely from the console."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import (
    Callable,
    Sequence,
)

from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.live_controller import (
    LiveCommerceController,
)
from app.youtube_auth import (
    build_youtube_service,
)
from app.youtube_live import (
    YouTubeLiveChatConnector,
)


OutputCallback = Callable[[str], None]
SleepCallback = Callable[[float], None]


def _http_error_reason(
    error: HttpError,
) -> str:
    """Extract a YouTube error reason without exposing details."""

    try:
        payload = json.loads(
            error.content.decode(
                "utf-8"
            )
        )
        errors = (
            payload
            .get("error", {})
            .get("errors", [])
        )

        if errors:
            return str(
                errors[0].get(
                    "reason",
                    "",
                )
            )

    except (
        AttributeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        pass

    return ""


def _format_youtube_error(
    error: Exception,
) -> str:
    """Return a safe user-facing YouTube error message."""

    if isinstance(
        error,
        RefreshError,
    ):
        return (
            "YouTube authorization expired. "
            "Authorize the application again."
        )

    if not isinstance(
        error,
        HttpError,
    ):
        return (
            "YouTube integration failed "
            "unexpectedly."
        )

    status_code = error.status_code
    reason = _http_error_reason(
        error
    )

    if reason in {
        "quotaExceeded",
        "dailyLimitExceeded",
        "rateLimitExceeded",
    }:
        return (
            "YouTube API quota has been reached. "
            "Try again after the quota resets."
        )

    if status_code == 401:
        return (
            "YouTube authorization expired. "
            "Authorize the application again."
        )

    if (
        status_code == 404
        or reason in {
            "liveChatDisabled",
            "liveChatEnded",
            "liveChatNotFound",
        }
    ):
        return (
            "The active YouTube Live Chat "
            "is no longer available."
        )

    if status_code == 429:
        return (
            "YouTube is receiving too many "
            "requests. Try again shortly."
        )

    return (
        "YouTube API request failed "
        f"with HTTP {status_code}."
    )


def run_read_only(
    *,
    connector: YouTubeLiveChatConnector,
    output_callback: OutputCallback = print,
    sleep_callback: SleepCallback = time.sleep,
    max_polls: int | None = None,
) -> int:
    """Read live chat without generating or sending replies."""

    live_chat_id = (
        connector.find_active_live_chat_id()
    )

    if live_chat_id is None:
        output_callback(
            "No active YouTube Live Chat "
            "was found."
        )
        return 1

    output_callback(
        "Connected to YouTube Live Chat."
    )

    page_token: str | None = None
    poll_count = 0

    while (
        max_polls is None
        or poll_count < max_polls
    ):
        page = connector.list_messages(
            live_chat_id,
            page_token=page_token,
        )

        for message in page.messages:
            author_name = (
                message.author_name
                or "Viewer"
            )
            output_callback(
                "YouTube "
                f"{author_name}: "
                f"{message.text}"
            )

        page_token = (
            page.next_page_token
        )
        poll_count += 1

        if (
            max_polls is not None
            and poll_count >= max_polls
        ):
            break

        sleep_callback(
            page.polling_interval_seconds
        )

    return 0

def _normalize_youtube_reply(
    text: str,
) -> str:
    """Normalize a reply to the YouTube chat limit."""

    normalized_text = " ".join(
        text.split()
    )

    if len(normalized_text) <= 200:
        return normalized_text

    return (
        normalized_text[:197].rstrip()
        + "..."
    )


def run_auto_reply(
    *,
    connector: YouTubeLiveChatConnector,
    controller: LiveCommerceController,
    output_callback: OutputCallback = print,
    sleep_callback: SleepCallback = time.sleep,
    max_polls: int | None = None,
) -> int:
    """Reply only to messages received after startup."""

    live_chat_id = (
        connector.find_active_live_chat_id()
    )

    if live_chat_id is None:
        output_callback(
            "No active YouTube Live Chat "
            "was found."
        )
        return 1

    output_callback(
        "Connected to YouTube Live Chat."
    )

    existing_page = (
        connector.list_messages(
            live_chat_id,
        )
    )
    page_token = (
        existing_page.next_page_token
    )
    polling_interval = (
        existing_page
        .polling_interval_seconds
    )

    output_callback(
        "AI auto-reply is active. "
        "Waiting for new messages."
    )

    poll_count = 0

    while (
        max_polls is None
        or poll_count < max_polls
    ):
        sleep_callback(
            polling_interval
        )

        page = connector.list_messages(
            live_chat_id,
            page_token=page_token,
        )

        for message in page.messages[:3]:
            response = (
                controller.process_message(
                    message.text,
                    platform="youtube",
                    speak_response=False,
                    metadata={
                        "youtube_message_id": (
                            message.message_id
                        ),
                        (
                            "youtube_"
                            "author_channel_id"
                        ): (
                            message
                            .author_channel_id
                        ),
                    },
                )
            )

            reply_text = (
                _normalize_youtube_reply(
                    response.text
                )
            )

            if (
                not response.allowed
                or not reply_text
            ):
                continue

            connector.send_message(
                live_chat_id=live_chat_id,
                text=reply_text,
            )
            output_callback(
                "AI replied to "
                f"{message.author_name or 'Viewer'}."
            )

        page_token = (
            page.next_page_token
        )
        polling_interval = (
            page.polling_interval_seconds
        )
        poll_count += 1

    return 0


def build_argument_parser(
) -> argparse.ArgumentParser:
    """Build command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Read an active YouTube "
            "Live Chat."
        ),
    )
    parser.add_argument(
        "--credentials",
        required=True,
        help=(
            "Path to the OAuth desktop "
            "client JSON file."
        ),
    )
    parser.add_argument(
        "--token",
        required=True,
        help=(
            "Path to the OAuth token "
            "JSON file."
        ),
    )
    mode_group = (
    parser
    .add_mutually_exclusive_group(
        required=True,
    )
)
    mode_group.add_argument(
    "--read-only",
    action="store_true",
    help=(
        "Read chat without sending "
        "any reply."
    ),
)
    mode_group.add_argument(
    "--auto-reply",
    action="store_true",
    help=(
        "Generate and send replies "
        "with the mock provider."
    ),
)

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Authorize and run the selected YouTube chat mode."""

    parser = build_argument_parser()
    arguments = parser.parse_args(
        argv
    )

    try:
        youtube = build_youtube_service(
            client_file=(
                arguments.credentials
            ),
            token_file=arguments.token,
        )
        connector = (
            YouTubeLiveChatConnector(
                youtube=youtube,
            )
        )

        if arguments.auto_reply:
            controller = (
                LiveCommerceController(
                    provider_name="mock",
                )
            )
            return run_auto_reply(
                connector=connector,
                controller=controller,
            )

        return run_read_only(
            connector=connector,
        )

    except (
        RefreshError,
        HttpError,
    ) as error:
        print(
            _format_youtube_error(
                error
            )
        )
        return 2

    except KeyboardInterrupt:
        print("")
        print(
            "YouTube Live Chat "
            "integration stopped."
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())