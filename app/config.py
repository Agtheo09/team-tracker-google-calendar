from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    timezone: str = "Europe/Athens"
    interval_hours: int = 6
    lookahead_days: int = 365
    game_duration_minutes: int = 150

    @property
    def timezone_obj(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def google_credentials(self) -> Path:
        return BASE_DIR / "credentials" / "credentials.json"

    @property
    def google_token(self) -> Path:
        return BASE_DIR / "credentials" / "token.json"

    @property
    def db_path(self) -> Path:
        return BASE_DIR / "data" / "sync.db"


SETTINGS = Settings()
