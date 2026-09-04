from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from app.config import SETTINGS
from app.sync import SyncWorker


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync configured basketball teams into Google Calendar."
    )
    parser.add_argument(
        "--once", action="store_true", help="Run a single sync and exit"
    )
    parser.add_argument(
        "--config", default="config.yaml", help="Path to team/competition config YAML"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    worker = SyncWorker(Path(args.config))
    try:
        while True:
            worker.run_once()
            if args.once:
                break
            time.sleep(SETTINGS.interval_hours * 60 * 60)
    except KeyboardInterrupt:
        logging.getLogger("basketball-sync").info("Stopping")
    finally:
        worker.close()


if __name__ == "__main__":
    main()
