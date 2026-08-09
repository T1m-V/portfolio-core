from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_core import PortfolioContext, active_context, save_data_directory, settings


def test_context_resolves_explicit_environment_and_saved_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "user_config_path", lambda *_args, **_kwargs: tmp_path / "user")
    monkeypatch.setenv("PORTFOLIO_DATA_DIR", str(tmp_path / "environment"))

    assert PortfolioContext.load(tmp_path / "explicit", load_secrets=False).paths.root == (
        tmp_path / "explicit"
    ).resolve()
    assert PortfolioContext.load(load_secrets=False).paths.root == (
        tmp_path / "environment"
    ).resolve()

    monkeypatch.delenv("PORTFOLIO_DATA_DIR")
    save_data_directory(tmp_path / "saved")
    assert PortfolioContext.load(load_secrets=False).paths.root == (tmp_path / "saved").resolve()


def test_context_requires_a_configured_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PORTFOLIO_DATA_DIR", raising=False)
    monkeypatch.setattr(settings, "user_config_path", lambda *_args, **_kwargs: tmp_path)

    with pytest.raises(RuntimeError, match="not configured"):
        PortfolioContext.load(load_secrets=False)


def test_context_loads_workspace_metadata_and_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "stock_metadata.json").write_text(
        '{"BTC": {"name": "Bitcoin"}}', encoding="utf-8"
    )
    (tmp_path / ".env").write_text("GETQUIN_TOKEN=test-token\n", encoding="utf-8")
    monkeypatch.delenv("GETQUIN_TOKEN", raising=False)

    context = PortfolioContext.from_root(tmp_path)

    assert context.stock_metadata() == {"BTC": {"name": "Bitcoin"}}
    assert context.currency_metadata() == {}
    assert context.getquin_token() == "test-token"


def test_context_activation_is_scoped(tmp_path: Path) -> None:
    context = PortfolioContext.from_root(tmp_path, load_secrets=False)

    with pytest.raises(RuntimeError, match="No PortfolioContext"):
        active_context()
    with context.activate():
        assert active_context() is context
    with pytest.raises(RuntimeError, match="No PortfolioContext"):
        active_context()


def test_paths_match_the_persisted_workspace_layout(tmp_path: Path) -> None:
    paths = PortfolioContext.from_root(tmp_path, load_secrets=False).paths
    expected = {
        "stock_metadata": "config/stock_metadata.json",
        "currency_metadata": "config/currency_metadata.json",
        "transaction_export": "transactions/transactions_export.json",
        "stock_split_export": "transactions/splits_export.json",
        "normalized_transactions": "transactions/getquin_data.csv",
        "portfolio_snapshot": "transactions/portfolio_snapshot.csv",
        "latest_prices": "latest_prices.csv",
        "chain_config": "config/chains.json",
        "tokens": "crypto/tokens",
        "crypto_transactions": "crypto/transactions",
        "crypto_snapshots": "crypto/snapshots",
        "block_map": "crypto/block_map",
        "protocol_underlying_tokens": "crypto/protocol_underlying_tokens",
        "accounting": "crypto/accounting",
        "dashboard_artifacts": "crypto/dashboard",
        "real_estate": "real_estate",
        "runtime": "runtime",
    }

    assert {name: getattr(paths, name) for name in expected} == {
        name: tmp_path / relative for name, relative in expected.items()
    }
    assert paths.direct_price("USD_EUR") == tmp_path / "prices" / "USD_EUR.csv"
    assert paths.lp_prices == tmp_path / "prices" / "lp_prices"
