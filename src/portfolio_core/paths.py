from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from portfolio_core.settings import PortfolioSettings


@dataclass(frozen=True, slots=True)
class PortfolioPaths:
    """All persisted portfolio paths rooted in one external data workspace."""

    root: Path

    @classmethod
    def from_settings(cls, settings: PortfolioSettings | None = None) -> PortfolioPaths:
        settings = settings or PortfolioSettings.load()
        return cls(root=settings.data_dir)

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


class LazyJsonMapping(Mapping[str, dict[str, Any]]):
    """Read JSON metadata on first use rather than during package import."""

    def __init__(self, path: Path):
        self.path = path
        self._data: dict[str, dict[str, Any]] | None = None

    def _load(self) -> dict[str, dict[str, Any]]:
        if self._data is None:
            if not self.path.exists():
                self._data = {}
            else:
                with self.path.open(encoding="utf-8") as metadata_file:
                    self._data = json.load(metadata_file)
        return self._data

    def __getitem__(self, key: str) -> dict[str, Any]:
        return self._load()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())

    def copy(self) -> dict[str, dict[str, Any]]:
        return self._load().copy()


PATHS = PortfolioPaths.from_settings()
DATA_FOLDER = PATHS.root
PRICES_FOLDER = PATHS.prices
LP_PRICES_FOLDER = PATHS.lp_prices
PRICE_DATA_FOLDER = PATHS.prices
TRANSACTION_DATA_FOLDER = PATHS.transactions

STOCK_METADATA_PATH = PATHS.config / "stock_metadata.json"
CURRENCY_METADATA_PATH = PATHS.config / "currency_metadata.json"
STOCK_METADATA: Mapping[str, dict[str, Any]] = LazyJsonMapping(STOCK_METADATA_PATH)
CURRENCY_METADATA: Mapping[str, dict[str, Any]] = LazyJsonMapping(CURRENCY_METADATA_PATH)

TRANSACTION_JSON_PATH = PATHS.transactions / "transactions_export.json"
STOCK_SPLIT_JSON_PATH = PATHS.transactions / "splits_export.json"
TRANSACTIONS_FILE_PATH = PATHS.transactions / "getquin_data.csv"
SNAPSHOT_FILE_PATH = PATHS.transactions / "portfolio_snapshot.csv"
SUMMARY_FILE_PATH = PATHS.root / "latest_prices.csv"

BLOCKCHAIN_FOLDER = PATHS.crypto
CHAIN_INFO_PATH = PATHS.config / "chains.json"
TOKENS_FOLDER = PATHS.crypto / "tokens"
BLOCKCHAIN_TRANSACTIONS_FOLDER = PATHS.crypto / "transactions"
BLOCKCHAIN_SNAPSHOT_FOLDER = PATHS.crypto / "snapshots"
BLOCKCHAIN_BLOCK_MAP_FOLDER = PATHS.crypto / "block_map"
PROTOCOL_UNDERLYING_TOKEN_FOLDER = PATHS.crypto / "protocol_underlying_tokens"
BLOCKCHAIN_ACCOUNTING_FOLDER = PATHS.crypto / "accounting"
BLOCKCHAIN_DASHBOARD_FOLDER = PATHS.crypto / "dashboard"

REAL_ESTATE_FOLDER = PATHS.real_estate
REAL_ESTATE_COSTS_FILE_NAME = "costs.csv"
REAL_ESTATE_INFLOWS_FILE_NAME = "inflows.csv"
REAL_ESTATE_VALUES_FILE_NAME = "values.csv"
REAL_ESTATE_OWNERSHIP_FILE_NAME = "ownership.csv"
REAL_ESTATE_MORTGAGE_GLOB = "*mortgage*.csv"

GETQUIN_URL = "https://api-gql-v2.getquin.com/"


def get_direct_price_file_path(symbol: str, prices_folder: Path | None = None) -> Path:
    return (prices_folder or PRICES_FOLDER) / f"{symbol}.csv"


def get_lp_price_file_path(
    *, chain: str, symbol: str, prices_folder: Path | None = None
) -> Path:
    return (prices_folder or PRICES_FOLDER) / "lp_prices" / chain / f"{symbol}.csv"
