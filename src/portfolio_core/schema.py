from __future__ import annotations

import tomllib
from pathlib import Path

_DATA_SCHEMA_VERSION = 1


def validate_data_workspace(root: Path) -> None:
    """Validate the external data workspace marker and schema version."""
    marker = root / "portfolio.toml"
    if not marker.exists():
        raise FileNotFoundError(f"Portfolio data marker is missing: {marker}")
    with marker.open("rb") as marker_file:
        config = tomllib.load(marker_file)
    version = config.get("schema_version")
    if version != _DATA_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported portfolio data schema {version!r}; expected {_DATA_SCHEMA_VERSION}"
        )
