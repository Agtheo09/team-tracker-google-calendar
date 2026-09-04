from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Game

SCOPES = ["https://www.googleapis.com/auth/calendar"]

MATCHES_CALENDAR_NAME = "Matches"
SYNC_MARKER = "basketball-calendar-sync"


class GoogleCalendar:
    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        calendar_id: str | None = None,
        reminders: list[dict[str, Any]] | None = None,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.reminders = reminders or []

        self.service = build(
            "calendar",
            "v3",
            credentials=self._load_credentials(),
            cache_discovery=False,
        )

        if calendar_id is None:
            self.calendar_id = self.get_or_create_matches_calendar()
        else:
            self.calendar_id = calendar_id

    def _load_credentials(self) -> Credentials:
        if not self.token_path.exists():
            raise RuntimeError(
                "Google OAuth token not found.\n" "Run:\n" "  python auth.py"
            )

        creds = Credentials.from_authorized_user_file(
            str(self.token_path),
            SCOPES,
        )

        if creds.valid:
            return creds

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

            self.token_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.token_path.write_text(
                creds.to_json(),
                encoding="utf-8",
            )

            return creds

        raise RuntimeError(
            "Google OAuth token is invalid.\n" "Run:\n" "  python auth.py"
        )

    def get_or_create_matches_calendar(self) -> str:
        page_token = None

        while True:
            response = (
                self.service.calendarList()
                .list(
                    pageToken=page_token,
                    maxResults=250,
                )
                .execute()
            )

            for calendar in response.get(
                "items",
                [],
            ):
                if calendar.get("summary") == MATCHES_CALENDAR_NAME:
                    return calendar["id"]

            page_token = response.get("nextPageToken")

            if not page_token:
                break

        created = (
            self.service.calendars()
            .insert(
                body={
                    "summary": MATCHES_CALENDAR_NAME,
                    "description": (
                        "Automatically synchronized " "basketball matches."
                    ),
                    "timeZone": "Europe/Athens",
                }
            )
            .execute()
        )

        return created["id"]

    @staticmethod
    def stable_event_id(game: Game) -> str:
        raw = (
            f"{game.source}|"
            f"{game.competition}|"
            f"{game.season}|"
            f"{game.source_id}"
        ).encode()

        return hashlib.sha1(raw).hexdigest()

    @staticmethod
    def _iso(dt: datetime) -> str:
        return dt.isoformat()

    @staticmethod
    def short_team_name(name: str) -> str:
        upper = name.upper()

        if "OLYMPIACOS" in upper:
            return "Olympiacos"

        if "PANATHINAIKOS" in upper:
            return "Panathinaikos"

        ignored = {
            "FC",
            "BC",
            "BASKETBALL",
        }

        words = [word for word in name.split() if word.upper() not in ignored]

        return " ".join(words[:2]) or name

    def _colour_for_game(
        self,
        game: Game,
    ) -> str | None:
        title = game.title.upper()

        if "OLYMPIACOS" in title:
            return "11"

        if "PANATHINAIKOS" in title:
            return "10"

        return None

    def event_body(
        self,
        game: Game,
    ) -> dict[str, Any]:

        home_short = self.short_team_name(game.home_team)

        away_short = self.short_team_name(game.away_team)

        # FULL names stay in the description.
        description = [
            (f"🏀 {game.home_team} " f"vs {game.away_team}"),
            f"Competition: {game.competition}",
            f"Season: {game.season}-{game.season + 1}",
        ]

        if game.round_name:
            description.append(f"Round: {game.round_name}")

        if game.venue:
            description.append(f"Venue: {game.venue}")

        if game.status:
            description.append(f"Status: {game.status}")

        if game.url:
            description.append(f"Source: {game.url}")

        body: dict[str, Any] = {
            "id": self.stable_event_id(game),
            "summary": (f"🏀 {home_short} - {away_short}"),
            "location": game.venue or "",
            "description": "\n".join(description),
            "start": {
                "dateTime": self._iso(game.start),
                "timeZone": "Europe/Athens",
            },
            "end": {
                "dateTime": self._iso(game.end),
                "timeZone": "Europe/Athens",
            },
            "reminders": {
                "useDefault": False,
                "overrides": self.reminders,
            },
            "extendedProperties": {
                "private": {
                    "basketball_sync": SYNC_MARKER,
                    "source": game.source,
                    "source_id": game.source_id,
                    "competition": game.competition,
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                }
            },
        }

        color_id = self._colour_for_game(game)

        if color_id:
            body["colorId"] = color_id

        return body

    def upsert(
        self,
        game: Game,
    ) -> tuple[str, bool]:

        body = self.event_body(game)
        event_id = body["id"]

        try:
            existing = (
                self.service.events()
                .get(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                )
                .execute()
            )

            old = {key: existing.get(key) for key in body if key != "id"}

            new = {key: body.get(key) for key in body if key != "id"}

            if old != new:
                (
                    self.service.events()
                    .update(
                        calendarId=self.calendar_id,
                        eventId=event_id,
                        body=body,
                        sendUpdates="none",
                    )
                    .execute()
                )

                return event_id, True

            return event_id, False

        except HttpError as exc:
            status = getattr(
                getattr(exc, "resp", None),
                "status",
                None,
            )

            if status != 404:
                raise

            (
                self.service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=body,
                    sendUpdates="none",
                )
                .execute()
            )

            return event_id, True
