# Basketball Calendar Sync

Automatically sync basketball matches for configurable teams to a dedicated **Google Calendar**.

Currently focused on **EuroLeague**. The project is designed to run continuously on a laptop, home server, or Docker host.

## Features

* Sync multiple teams from configuration
* Currently supports EuroLeague
* Automatically creates a dedicated `Matches` Google Calendar
* Does not use your primary calendar
* Correct `Europe/Athens` timezone handling
* Automatically updates games when their schedule changes
* Prevents duplicate events with stable event IDs
* Configurable Google Calendar event colors
* Configurable reminders
* Configurable sync interval and lookahead period
* Runs continuously with Docker
* Supports one-shot syncs for testing
* Google OAuth authentication with a one-time browser login

## Requirements

* Windows, Linux, or macOS
* Python 3.12+
* Docker Desktop / Docker Engine
* A Google account
* A Google Cloud project with the Google Calendar API enabled

## Project structure

```text
team-tracker-google-calendar/
├── app/
│   ├── providers/
│   │   └── euroleague.py
│   ├── config.py
│   ├── database.py
│   ├── google_calendar.py
│   ├── models.py
│   ├── sync.py
│   └── team_config.py
│
├── credentials/
│   └── .gitkeep
├── data/
│   └── .gitkeep
│
├── auth.py
├── cleanup.py
├── main.py
├── config.yaml
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── start.ps1
```

## 1. Google Cloud setup

Open:

https://console.cloud.google.com/

Create a project.

Enable:

**Google Calendar API**

Then configure Google OAuth:

1. Open **Google Auth Platform**
2. Configure the OAuth consent screen
3. Add yourself as a test user
4. Create an OAuth client
5. Choose **Desktop app**
6. Download the client JSON

Rename the downloaded file:

```text
credentials.json
```

Place it here:

```text
credentials/credentials.json
```

Do not commit this file.

## 2. First authentication

Create and activate a virtual environment:

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python auth.py
```

A browser window will open.

Sign in with the Google account whose calendar you want to use and approve access.

A token will be saved as:

```text
credentials/token.json
```

Do not commit it.

## 3. Configuration

Create `config.yaml` in the project root.

Example:

```yaml
timezone: Europe/Athens

sync:
  interval_hours: 6
  lookahead_days: 365

calendar:
  name: Matches

game:
  duration_minutes: 150

  reminders:
    - method: popup
      minutes: 60

    - method: popup
      minutes: 15

teams:
  - key: olympiacos
    name: Olympiacos
    display_name: Olympiacos
    provider_codes:
      euroleague: OLY
    color_id: "11"
    enabled: true

  - key: panathinaikos
    name: Panathinaikos
    display_name: Panathinaikos
    provider_codes:
      euroleague: PAN
    color_id: "10"
    enabled: true

competitions:
  - euroleague
```

### Adding another team

Add another entry:

```yaml
  - key: real_madrid
    name: Real Madrid
    display_name: Real Madrid
    provider_codes:
      euroleague: RMA
    color_id: "9"
    enabled: true
```

The team code must match the provider's team code.

## 4. Run once for testing

Before running continuously:

```bash
python main.py --once
```

Or with Docker:

```bash
docker compose run --rm basketball-calendar-sync python main.py --once
```

This performs one synchronization and exits.

## 5. Run continuously with Docker

Build and start:

```bash
docker compose up -d --build
```

Check the logs:

```bash
docker compose logs -f
```

The worker will:

1. Fetch the configured schedules
2. Filter the configured teams
3. Create/update events
4. Wait for the configured interval
5. Repeat

With:

```yaml
sync:
  interval_hours: 6
```

the schedule is checked approximately every six hours.

## 6. Start everything on Windows

The repository includes:

```text
start.ps1
```

Run:

```powershell
.\start.ps1
```

The script checks OAuth setup, builds the Docker image, and starts the worker.

## 7. Google Calendar

The worker automatically creates or reuses:

```text
Matches
```

All synchronized games are written there.

Your primary Google Calendar is not used for synchronized events.

This makes it easy to toggle match events on or off from Google Calendar.

## 8. Event format

Example title:

```text
🏀 Olympiacos - Real Madrid
```

The description contains the complete team names and match information:

```text
🏀 OLYMPIACOS PIRAEUS vs REAL MADRID
Competition: EuroLeague
Season: 2026-2027
Round: 4
Venue: ...
Source: ...
```

The event timezone is:

```text
Europe/Athens
```

## 9. Event colours

Each team can define its Google Calendar event color:

```yaml
color_id: "11"
```

Example:

```yaml
Olympiacos:
  color_id: "11"

Panathinaikos:
  color_id: "10"
```

Change the ID in `config.yaml` to use another Google Calendar color.

## 10. Automatic schedule updates

Events use deterministic IDs based on:

```text
source
competition
season
game ID
```

This means repeated syncs do not create duplicate events.

When the source schedule changes, the existing Google Calendar event is updated.

Examples:

* tip-off time changes
* venue changes
* event title changes
* reminders change
* team information changes

## 11. Stopping the worker

Stop and remove the Docker container:

```bash
docker compose down
```

This does not delete your Google Calendar or synchronized events.

To start again:

```bash
docker compose up -d
```

## 12. Logs

View recent logs:

```bash
docker compose logs --tail=100
```

Follow logs live:

```bash
docker compose logs -f
```

## 13. Cleaning synchronized events

`cleanup.py` removes basketball events created by this project from the `Matches` calendar and clears the local sync database.

Run:

```bash
python cleanup.py
```

Use this when you want a completely fresh synchronization.

## 14. Security

Never commit:

```text
credentials/credentials.json
credentials/token.json
.env
data/
```

These files are intentionally ignored by Git.

Check before committing:

```bash
git status
```

Also check tracked files:

```bash
git ls-files credentials
git ls-files .env
git ls-files data
```

Those commands should return nothing.

## 15. Git workflow

After making code changes:

```bash
git status
git add -A
git commit -m "Describe change"
git push
```

For configuration changes that should remain local, edit `config.yaml` without committing it.

## 16. Troubleshooting

### Google authentication fails

Delete:

```text
credentials/token.json
```

Then run:

```bash
python auth.py
```

again.

### Docker says `config.yaml` does not exist

Create `config.yaml` in the project root.

### The worker is not running

Check:

```bash
docker compose ps
```

Then:

```bash
docker compose logs
```

### Games appear at the wrong time

Verify:

```yaml
timezone: Europe/Athens
```

and rebuild the container after code changes:

```bash
docker compose up -d --build
```

### Duplicate events appear

Run:

```bash
python cleanup.py
```

Then:

```bash
docker compose up -d --build
```

## License

MIT
