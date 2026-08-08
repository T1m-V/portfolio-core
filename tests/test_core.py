from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from portfolio_core import WorkspaceLockedError, active_context, mutation_session
from portfolio_core.context import PortfolioContext
from portfolio_core.paths import PortfolioPaths
from portfolio_core.price_history import get_forex_rate, merge_price_frames
from portfolio_core.schema import validate_data_workspace
from portfolio_core.settings import PortfolioSettings


def test_explicit_data_directory_wins(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit"
    settings = PortfolioSettings.load(
        explicit,
        environ={"PORTFOLIO_DATA_DIR": str(tmp_path / "ignored")},
        load_secrets=False,
    )

    assert settings.data_dir == explicit.resolve()
    assert PortfolioPaths.from_root(settings.data_dir).prices == explicit.resolve() / "prices"


def test_environment_data_directory_uses_portfolio_name(tmp_path: Path) -> None:
    preferred = PortfolioSettings.load(
        environ={"PORTFOLIO_DATA_DIR": str(tmp_path / "preferred")},
        load_secrets=False,
    )
    assert preferred.data_dir == (tmp_path / "preferred").resolve()


def test_context_loads_metadata_from_explicit_workspace(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "stock_metadata.json").write_text(
        '{"BTC": {"name": "Bitcoin"}}', encoding="utf-8"
    )
    context = PortfolioContext.from_root(tmp_path, load_secrets=False)

    assert context.stock_metadata()["BTC"]["name"] == "Bitcoin"
    assert context.currency_metadata() == {}


def test_context_activation_is_scoped(tmp_path: Path) -> None:
    context = PortfolioContext.from_root(tmp_path, load_secrets=False)
    with pytest.raises(RuntimeError, match="No PortfolioContext"):
        active_context()

    with context.activate():
        assert active_context() is context

    with pytest.raises(RuntimeError, match="No PortfolioContext"):
        active_context()


def test_mutation_session_serializes_and_records_runs(tmp_path: Path) -> None:
    context = PortfolioContext.from_root(tmp_path, load_secrets=False)
    with mutation_session(paths=context.paths, component="test", version="1.0"):
        with pytest.raises(WorkspaceLockedError):
            with mutation_session(paths=context.paths, component="other", version="1.0"):
                pass

    assert not (context.paths.runtime / "mutation.lock").exists()
    manifest = (context.paths.runtime / "manifests" / "test.json").read_text(
        encoding="utf-8"
    )
    assert '"status": "completed"' in manifest


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
    assert get_forex_rate(currency="USD", date="2026-01-01", prices_folder=prices) == 1.5


def test_getquin_token_comes_from_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GETQUIN_TOKEN", "secret-token")
    context = PortfolioContext.from_root(tmp_path, load_secrets=False)

    assert context.getquin_token() == "secret-token"

    monkeypatch.delenv("GETQUIN_TOKEN")
    os.environ.pop("GETQUIN_TOKEN", None)

    with pytest.raises(RuntimeError, match="GETQUIN_TOKEN"):
        context.getquin_token()
