from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import hashlib
import requests
from icalendar import Calendar

from ..models import Game, Team


class GBLProvider:
    source_name = "gbl"

    def __init__(
        self,
        ics_url: str,
        timezone: str = "Europe/Athens",
        duration_minutes: int = 150,
    ) -> None:
        self.ics_url = ics_url
        self.tz = ZoneInfo(timezone)
        self.duration = timedelta(minutes=duration_minutes)

    @staticmethod
    def _text(value) -> str:
        if value is None:
            return ""

        if hasattr(value, "to_ical"):
            value = value.to_ical()

        if isinstance(value, bytes):
            return value.decode(
                "utf-8",
                errors="ignore",
            )

        return str(value).strip()

    def _local_datetime(
        self,
        value,
    ) -> datetime:
        if hasattr(value, "dt"):
            value = value.dt

        if isinstance(value, datetime):
            dt = value
        else:
            raise ValueError(f"Unsupported ICS datetime: {value!r}")

        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.tz)

        return dt.astimezone(self.tz)

    @staticmethod
    def _matches_team(
        team: Team,
        home: str,
        away: str,
    ) -> bool:
        wanted = team.name.lower()

        return (
            wanted in home.lower()
            or wanted in away.lower()
            or (team.display_name.lower() in home.lower())
            or (team.display_name.lower() in away.lower())
        )

    def fetch(
        self,
        teams: list[Team],
        start: datetime,
        end: datetime,
    ) -> list[Game]:

        if not self.ics_url:
            print("GBL: no ICS URL configured; skipping.")
            return []

        response = requests.get(
            self.ics_url,
            timeout=30,
            headers={"User-Agent": ("basketball-calendar-sync/1.0")},
        )

        response.raise_for_status()

        calendar = Calendar.from_ical(response.content)

        wanted_teams = [team for team in teams if team.enabled]

        games: list[Game] = []

        for component in calendar.walk():

            if component.name != "VEVENT":
                continue

            start_value = component.get("DTSTART")

            if start_value is None:
                continue

            game_start = self._local_datetime(start_value)

            if not (start.astimezone(self.tz) <= game_start <= end.astimezone(self.tz)):
                continue

            summary = self._text(component.get("SUMMARY"))

            location = self._text(component.get("LOCATION"))

            uid = self._text(component.get("UID"))

            description = self._text(component.get("DESCRIPTION"))

            if not uid:
                uid = hashlib.sha1(
                    (f"{game_start.isoformat()}|" f"{summary}|" f"{location}").encode()
                ).hexdigest()

            # ECAL events normally contain the matchup in SUMMARY.
            parts = [part.strip() for part in summary.split(" vs ")]

            if len(parts) != 2:
                parts = [part.strip() for part in summary.split(" - ")]

            if len(parts) != 2:
                continue

            home = parts[0]
            away = parts[1]

            if not any(
                self._matches_team(
                    team,
                    home,
                    away,
                )
                for team in wanted_teams
            ):
                continue

            games.append(
                Game(
                    source=self.source_name,
                    source_id=uid,
                    competition=("Greek Basketball League"),
                    season=game_start.year,
                    home_team=home,
                    away_team=away,
                    start=game_start,
                    end=game_start + self.duration,
                    venue=location or None,
                    round_name=None,
                    status=None,
                    url=self.ics_url,
                )
            )

        print(f"GBL: found {len(games)} matching games.")

        return games
