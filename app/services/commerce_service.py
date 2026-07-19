from __future__ import annotations

from app.services.models import CommerceResponse


class CommerceService:
    """
    Main Business Service.

    This service will become the single entry point
    for every AI interaction.

    Current status:
        Sprint 30 Foundation
    """

    def __init__(self) -> None:
        pass

    def process_message(
        self,
        message: str,
        *,
        platform: str = "generic",
    ) -> CommerceResponse:
        """
        Process customer message.

        Full implementation will be migrated
        from BakeryDemo during Sprint 30.
        """

        raise NotImplementedError(
            "Sprint 30 migration in progress."
        )