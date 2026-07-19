from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CommerceResponse:
    """
    Standard response returned by CommerceService.

    This model is transport-independent and can be used by
    Console, LINE, TikTok, OBS and Web API.
    """

    text: str

    allowed: bool = True

    risk_score: float = 0.0

    compliance_score: float = 100.0

    execution_time_ms: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )