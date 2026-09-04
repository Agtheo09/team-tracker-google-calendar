from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Team:
    key: str
    name: str
    display_name: str
    provider_codes: dict[str, str]
    color_id: str | None = None
    enabled: bool = True

    @property
    def provider_code(self) -> str:
        # Backwards compatibility for EuroLeague.
        return self.provider_codes.get(
            "euroleague",
            "",
        )


@dataclass(frozen=True)
class Game:
    source: str
    source_id: str
    competition: str
    season: int

    home_team: str
    away_team: str

    start: datetime
    end: datetime

    venue: str | None = None
    round_name: str | None = None
    status: str | None = None
    url: str | None = None

    @property
    def title(self) -> str:
        return f"{self.home_team} vs " f"{self.away_team}"
