from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PortfolioPaths:
    """All persisted paths rooted in one explicit portfolio data workspace."""

    root: Path

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def prices(self) -> Path:
        return self.root / "prices"

    @property
    def lp_prices(self) -> Path:
        return self.prices / "lp_prices"

    @property
    def transactions(self) -> Path:
        return self.root / "transactions"

    @property
    def crypto(self) -> Path:
        return self.root / "crypto"

    @property
    def real_estate(self) -> Path:
        return self.root / "real_estate"

    @property
    def runtime(self) -> Path:
        return self.root / "runtime"

    @property
    def stock_metadata(self) -> Path:
        return self.config / "stock_metadata.json"

    @property
    def currency_metadata(self) -> Path:
        return self.config / "currency_metadata.json"

    @property
    def transaction_export(self) -> Path:
        return self.transactions / "transactions_export.json"

    @property
    def stock_split_export(self) -> Path:
        return self.transactions / "splits_export.json"

    @property
    def normalized_transactions(self) -> Path:
        return self.transactions / "getquin_data.csv"

    @property
    def portfolio_snapshot(self) -> Path:
        return self.transactions / "portfolio_snapshot.csv"

    @property
    def latest_prices(self) -> Path:
        return self.root / "latest_prices.csv"

    @property
    def chain_config(self) -> Path:
        return self.config / "chains.json"

    @property
    def tokens(self) -> Path:
        return self.crypto / "tokens"

    @property
    def crypto_transactions(self) -> Path:
        return self.crypto / "transactions"

    @property
    def crypto_snapshots(self) -> Path:
        return self.crypto / "snapshots"

    @property
    def block_map(self) -> Path:
        return self.crypto / "block_map"

    @property
    def protocol_underlying_tokens(self) -> Path:
        return self.crypto / "protocol_underlying_tokens"

    @property
    def accounting(self) -> Path:
        return self.crypto / "accounting"

    @property
    def dashboard_artifacts(self) -> Path:
        return self.crypto / "dashboard"

    def direct_price(self, symbol: str) -> Path:
        return self.prices / f"{symbol}.csv"
