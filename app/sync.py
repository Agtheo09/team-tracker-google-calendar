from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

from .config import SETTINGS
from .google_calendar import GoogleCalendar
from .providers.euroleague import EuroLeagueProvider
from .providers.gbl import GBLProvider
from .team_config import (
    load_competitions,
    load_config,
    load_teams,
)

LOG = logging.getLogger("basketball-sync")


class SyncWorker:
    def __init__(
        self,
        config_path: Path,
    ) -> None:

        self.config_path = config_path

        config = load_config(config_path)

        self.teams = load_teams(config_path)

        self.competitions = load_competitions(config_path)

        self.calendar = GoogleCalendar(
            SETTINGS.google_credentials,
            SETTINGS.google_token,
            None,
            reminders=config.get(
                "game",
                {},
            ).get(
                "reminders",
                [],
            ),
        )

        duration = config.get(
            "game",
            {},
        ).get(
            "duration_minutes",
            150,
        )

        gbl_url = (
            config.get(
                "providers",
                {},
            )
            .get(
                "gbl",
                {},
            )
            .get(
                "ics_url",
                "",
            )
        )

        self.providers = {
            "euroleague": EuroLeagueProvider(
                SETTINGS.timezone,
                duration,
            ),
            "gbl": GBLProvider(
                gbl_url,
                SETTINGS.timezone,
                duration,
            ),
        }

    def run_once(self) -> None:

        now = datetime.now(SETTINGS.timezone_obj)

        end = now + timedelta(days=SETTINGS.lookahead_days)

        total = 0
        changed = 0

        for competition in self.competitions:

            name = competition.lower()

            provider = self.providers.get(name)

            if provider is None:
                LOG.warning(
                    "No provider: %s",
                    competition,
                )
                continue

            try:
                games = provider.fetch(
                    self.teams,
                    now,
                    end,
                )
            except Exception:
                LOG.exception(
                    "Provider failed: %s",
                    competition,
                )
                continue

            for game in games:

                total += 1

                event_id, did_change = self.calendar.upsert(game)

                if did_change:
                    changed += 1

                    LOG.info(
                        "Synced: %s (%s)",
                        game.title,
                        event_id,
                    )

        LOG.info(
            "Sync complete: %d games, " "%d calendar changes",
            total,
            changed,
        )

    def run_forever(self) -> None:

        while True:

            try:
                self.run_once()

            except Exception:
                LOG.exception("Unexpected sync failure")

            interval = SETTINGS.interval_hours * 3600

            LOG.info(
                "Next sync in %d hours.",
                SETTINGS.interval_hours,
            )

            time.sleep(interval)
