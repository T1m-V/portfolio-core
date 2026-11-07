from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

from platformdirs import user_config_path

DATA_DIR_ENV = "PORTFOLIO_DATA_DIR"


def _config_path() -> Path:
    return user_config_path("portfolio", appauthor=False) / "config.toml"


def resolve_data_directory(data_dir: str | Path | None = None) -> Path:
    """Resolve an explicit, environment, or persisted user workspace."""
    if data_dir is not None:
        return Path(data_dir).expanduser().resolve()

    if value := os.environ.get(DATA_DIR_ENV):
        return Path(value).expanduser().resolve()

    config_path = _config_path()
    if not config_path.exists():
        raise RuntimeError(
            f"Portfolio data directory is not configured; set {DATA_DIR_ENV} or call "
            "save_data_directory(PATH)"
        )
    with config_path.open("rb") as config_file:
        config = tomllib.load(config_file)
    try:
        return Path(config["data"]["directory"]).expanduser().resolve()
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Portfolio data directory is missing from {config_path}") from exc


def save_data_directory(data_dir: str | Path) -> Path:
    """Persist the preferred data directory in the user configuration folder."""
    resolved = Path(data_dir).expanduser().resolve()
    config_path = _config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(f"[data]\ndirectory = {json.dumps(str(resolved))}\n", encoding="utf-8")
    return config_path
