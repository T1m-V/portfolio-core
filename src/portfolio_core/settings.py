from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_config_path, user_data_path

DATA_DIR_ENV = "PORTFOLIO_DATA_DIR"


def _configured_data_dir() -> Path | None:
    config_path = user_config_path("portfolio-dashboard", appauthor=False) / "config.toml"
    if not config_path.exists():
        return None
    with config_path.open("rb") as config_file:
        config = tomllib.load(config_file)
    value = config.get("data", {}).get("directory")
    return Path(value).expanduser() if value else None


@dataclass(frozen=True, slots=True)
class PortfolioSettings:
    """Runtime settings shared by portfolio applications."""

    data_dir: Path

    @classmethod
    def load(
        cls,
        data_dir: str | Path | None = None,
        *,
        environ: Mapping[str, str] | None = None,
        load_secrets: bool = True,
    ) -> PortfolioSettings:
        """Resolve the portfolio data directory and optional local secrets."""
        env = os.environ if environ is None else environ
        configured = Path(data_dir).expanduser() if data_dir else None
        if configured is None and (value := env.get(DATA_DIR_ENV)):
            configured = Path(value).expanduser()
        if configured is None:
            configured = _configured_data_dir()
        if configured is None:
            configured = user_data_path("portfolio-data", appauthor=False)

        resolved = configured.resolve()
        if load_secrets:
            load_dotenv(resolved / ".env", override=False)
        return cls(data_dir=resolved)


def save_data_directory(data_dir: str | Path) -> Path:
    """Persist the preferred data directory in the user configuration folder."""
    resolved = Path(data_dir).expanduser().resolve()
    config_dir = user_config_path("portfolio-dashboard", appauthor=False)
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"
    escaped = str(resolved).replace("\\", "\\\\").replace('"', '\\"')
    config_path.write_text(f'[data]\ndirectory = "{escaped}"\n', encoding="utf-8")
    return config_path
