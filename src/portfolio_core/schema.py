from __future__ import annotations

import tomllib
from pathlib import Path

DATA_SCHEMA_VERSION = 1


def validate_data_workspace(root: Path, *, allow_missing: bool = False) -> None:
    """Validate the external data workspace marker and schema version."""
    marker = root / "portfolio.toml"
    if not marker.exists():
        if allow_missing:
            return
        raise FileNotFoundError(f"Portfolio data marker is missing: {marker}")
    with marker.open("rb") as marker_file:
        config = tomllib.load(marker_file)
    version = config.get("schema_version")
    if version != DATA_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported portfolio data schema {version!r}; expected {DATA_SCHEMA_VERSION}"
        )
