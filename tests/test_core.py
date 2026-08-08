from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from portfolio_core.paths import LazyJsonMapping, PortfolioPaths
from portfolio_core.price_history import get_forex_rate, merge_price_frames
from portfolio_core.schema import validate_data_workspace
from portfolio_core.settings import PortfolioSettings, get_token


def test_explicit_data_directory_wins(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit"
    settings = PortfolioSettings.load(
        explicit,
        environ={"PORTFOLIO_DATA_DIR": str(tmp_path / "ignored")},
        load_secrets=False,
    )

    assert settings.data_dir == explicit.resolve()
    assert PortfolioPaths.from_settings(settings).prices == explicit.resolve() / "prices"


def test_environment_data_directory_supports_new_and_legacy_names(tmp_path: Path) -> None:
    preferred = PortfolioSettings.load(
        environ={"PORTFOLIO_DATA_DIR": str(tmp_path / "preferred")},
        load_secrets=False,
    )
    legacy = PortfolioSettings.load(
        environ={"STOCKDATA_DATA_DIR": str(tmp_path / "legacy")},
        load_secrets=False,
    )

    assert preferred.data_dir == (tmp_path / "preferred").resolve()
    assert legacy.data_dir == (tmp_path / "legacy").resolve()


def test_metadata_is_loaded_lazily(tmp_path: Path) -> None:
    metadata_path = tmp_path / "assets.json"
    metadata = LazyJsonMapping(metadata_path)
    assert not metadata

    metadata_path.write_text(json.dumps({"BTC": {"name": "Bitcoin"}}), encoding="utf-8")
    fresh_metadata = LazyJsonMapping(metadata_path)
    assert fresh_metadata["BTC"]["name"] == "Bitcoin"


def test_data_schema_marker_is_required_and_versioned(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_data_workspace(tmp_path)

    (tmp_path / "portfolio.toml").write_text("schema_version = 1\n", encoding="utf-8")
    validate_data_workspace(tmp_path)

    (tmp_path / "portfolio.toml").write_text("schema_version = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported portfolio data schema"):
        validate_data_workspace(tmp_path)


def test_incoming_prices_win_and_forex_uses_as_of_date(tmp_path: Path) -> None:
    merged = merge_price_frames(
        existing=pd.DataFrame({"Date": ["2026-01-01"], "Price": [1.0]}),
        incoming=pd.DataFrame(
            {"Date": ["2026-01-02", "2026-01-01"], "Price": [2.0, 1.5]}
        ),
    )
    assert merged.to_dict("records") == [
        {"Date": "2026-01-02", "Price": 2.0},
        {"Date": "2026-01-01", "Price": 1.5},
    ]

    prices = tmp_path / "prices"
    prices.mkdir()
    merged.to_csv(prices / "USD_EUR.csv", index=False)
    assert get_forex_rate("USD", "2026-01-01", prices) == 1.5


def test_get_token_supports_ignored_credential_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "getquin-token.txt").write_text("secret-token\n", encoding="utf-8")
    monkeypatch.setenv("PORTFOLIO_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("GETQUIN_TOKEN", raising=False)

    assert get_token() == "secret-token"
