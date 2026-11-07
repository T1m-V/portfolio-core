from __future__ import annotations

from pathlib import Path

import pytest

from portfolio_core import PortfolioContext, active_context, save_data_directory, settings


def test_context_resolves_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "user_config_path", lambda *_args, **_kwargs: tmp_path / "user")
    monkeypatch.delenv("PORTFOLIO_DATA_DIR", raising=False)

    with pytest.raises(RuntimeError, match="not configured"):
        PortfolioContext.load(load_secrets=False)

    assert PortfolioContext.load(tmp_path / "explicit", load_secrets=False).paths.root == (
        tmp_path / "explicit"
    ).resolve()

    monkeypatch.setenv("PORTFOLIO_DATA_DIR", str(tmp_path / "environment"))
    assert PortfolioContext.load(load_secrets=False).paths.root == (
        tmp_path / "environment"
    ).resolve()

    monkeypatch.delenv("PORTFOLIO_DATA_DIR")
    save_data_directory(tmp_path / "saved")
    assert PortfolioContext.load(load_secrets=False).paths.root == (tmp_path / "saved").resolve()


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

    context = PortfolioContext.load(tmp_path)

    assert context.stock_metadata() == {"BTC": {"name": "Bitcoin"}}
    assert context.currency_metadata() == {}
    assert context.getquin_token() == "test-token"


def test_context_activation_is_scoped(tmp_path: Path) -> None:
    context = PortfolioContext.load(tmp_path, load_secrets=False)

    with pytest.raises(RuntimeError, match="No PortfolioContext"):
        active_context()
    with context.activate():
        assert active_context() is context
    with pytest.raises(RuntimeError, match="No PortfolioContext"):
        active_context()
