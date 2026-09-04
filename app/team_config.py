from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Team


def _load(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle) or {}


def load_teams(
    path: Path,
) -> list[Team]:

    config = _load(path)

    result = []

    for raw in config.get(
        "teams",
        [],
    ):
        result.append(
            Team(
                key=str(raw["key"]),
                name=str(raw["name"]),
                display_name=str(
                    raw.get(
                        "display_name",
                        raw["name"],
                    )
                ),
                provider_codes={
                    str(k): str(v)
                    for k, v in raw.get(
                        "provider_codes",
                        {},
                    ).items()
                },
                color_id=(str(raw["color_id"]) if raw.get("color_id") else None),
                enabled=bool(raw.get("enabled", True)),
            )
        )

    return result


def load_competitions(
    path: Path,
) -> list[str]:

    config = _load(path)

    return [
        str(value)
        for value in config.get(
            "competitions",
            [],
        )
    ]


def load_config(
    path: Path,
) -> dict[str, Any]:

    return _load(path)
