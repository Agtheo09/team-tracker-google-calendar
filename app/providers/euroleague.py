from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from euroleague_api.schedule import Schedule

from ..models import Game, Team


class EuroLeagueProvider:
    source_name = "euroleague"
    competition_code = "E"

    def __init__(
        self,
        timezone: str = "Europe/Athens",
        duration_minutes: int = 150,
    ) -> None:
        self.tz = ZoneInfo(timezone)
        self.duration = timedelta(minutes=duration_minutes)

    @staticmethod
    def _season(dt: datetime) -> int:
        return dt.year if dt.month >= 7 else dt.year - 1

    def _parse_game_datetime(
        self,
        row: pd.Series,
    ) -> datetime | None:

        # ACTUAL EuroLeague API fields:
        # date     = game date
        # startime = game start time
        #
        # confirmeddate / confirmedtime are boolean flags
        # and must NOT be used as date/time values.

        date_value = row.get("date")
        time_value = row.get("startime")

        if date_value is None or pd.isna(date_value):
            return None

        if time_value is None or pd.isna(time_value):
            return None

        raw = (
            f"{str(date_value).strip()} "
            f"{str(time_value).strip()}"
        )

        parsed = pd.to_datetime(
            raw,
            errors="coerce",
        )

        if pd.isna(parsed):
            print(
                f"WARNING: Could not parse datetime: {raw}"
            )
            return None

        dt = parsed.to_pydatetime()

        # Treat API time as local game time in Athens.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)
        else:
            dt = dt.astimezone(self.tz)

        return dt

    def fetch(
        self,
        teams: list[Team],
        start: datetime,
        end: datetime,
    ) -> list[Game]:

        schedule = Schedule(self.competition_code)

        season = self._season(start)

        print(
            f"Fetching EuroLeague season {season}..."
        )

        df = schedule.get_schedule(season)

        if df is None or df.empty:
            print(
                "EuroLeague API returned no games."
            )
            return []

        print(
            f"EuroLeague API returned {len(df)} rows."
        )

        wanted = {
            team.provider_code.upper()
            for team in teams
            if team.enabled
        }

        print(
            f"Configured team codes: {sorted(wanted)}"
        )

        games: list[Game] = []

        start_local = start.astimezone(self.tz)
        end_local = end.astimezone(self.tz)

        for _, row in df.iterrows():

            home_code = str(
                row.get("homecode") or ""
            ).strip().upper()

            away_code = str(
                row.get("awaycode") or ""
            ).strip().upper()

            if not ({home_code, away_code} & wanted):
                continue

            game_dt = self._parse_game_datetime(row)

            if game_dt is None:
                continue

            if not (
                start_local <= game_dt <= end_local
            ):
                continue

            game_code = row.get("gamecode")

            if (
                game_code is None
                or pd.isna(game_code)
            ):
                continue

            home_name = str(
                row.get("hometeam") or home_code
            )

            away_name = str(
                row.get("awayteam") or away_code
            )

            venue = row.get("arenaname")
            round_name = row.get("round")

            games.append(
                Game(
                    source=self.source_name,
                    source_id=str(game_code),
                    competition="EuroLeague",
                    season=season,
                    home_team=home_name,
                    away_team=away_name,
                    start=game_dt,
                    end=game_dt + self.duration,
                    venue=(
                        str(venue)
                        if venue is not None
                        and not pd.isna(venue)
                        else None
                    ),
                    round_name=(
                        str(round_name)
                        if round_name is not None
                        and not pd.isna(round_name)
                        else None
                    ),
                    status=None,
                )
            )

        print(
            f"Found {len(games)} matching games."
        )

        return games
