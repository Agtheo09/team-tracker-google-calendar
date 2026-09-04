from __future__ import annotations

from app.config import SETTINGS
from app.google_calendar import GoogleCalendar


def main() -> None:
    # Explicitly target the Matches calendar.
    calendar = GoogleCalendar(
        SETTINGS.google_credentials,
        SETTINGS.google_token,
        None,
    )

    service = calendar.service
    calendar_id = calendar.calendar_id

    deleted = 0
    page_token = None

    while True:
        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                showDeleted=False,
                maxResults=2500,
                pageToken=page_token,
            )
            .execute()
        )

        for event in response.get("items", []):
            summary = event.get("summary", "")

            # Delete only events created by this worker.
            marker = (
                event.get("extendedProperties", {})
                .get("private", {})
                .get("basketball_sync")
            )

            if marker != "basketball-calendar-sync":
                continue

            print(f"Deleting: {summary}")

            service.events().delete(
                calendarId=calendar_id,
                eventId=event["id"],
            ).execute()

            deleted += 1

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    if SETTINGS.db_path.exists():
        SETTINGS.db_path.unlink()

    print()
    print(f"Deleted {deleted} basketball events " f"from the Matches calendar.")


if __name__ == "__main__":
    main()
