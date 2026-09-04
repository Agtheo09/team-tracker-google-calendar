from __future__ import annotations

import argparse
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-time Google Calendar OAuth bootstrap"
    )
    parser.add_argument(
        "--credentials",
        default="credentials/credentials.json",
    )
    parser.add_argument(
        "--token",
        default="credentials/token.json",
    )
    args = parser.parse_args()

    credentials_path = Path(args.credentials)
    token_path = Path(args.token)

    if not credentials_path.exists():
        raise SystemExit(f"Missing OAuth client JSON: {credentials_path}")

    if token_path.exists():
        print(f"Token already exists: {token_path}")
        print("Delete it only if you want to authorize again.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        SCOPES,
    )

    # This runs on Windows, so the normal browser can be opened here.
    creds = flow.run_local_server(
        port=0,
        open_browser=True,
    )

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(
        creds.to_json(),
        encoding="utf-8",
    )

    print()
    print("Google authorization complete.")
    print(f"Token saved to: {token_path}")
    print()
    print("You can now run:")
    print("docker compose up -d")


if __name__ == "__main__":
    main()
