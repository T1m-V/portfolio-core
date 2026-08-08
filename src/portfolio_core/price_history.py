from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from portfolio_core.workspace import atomic_write_csv

PRICE_COLUMNS = ["Date", "Price"]


def normalize_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return canonical descending Date/Price rows."""
    if frame.empty:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    if not set(PRICE_COLUMNS).issubset(frame.columns):
        return pd.DataFrame(columns=PRICE_COLUMNS)
    canonical = frame.loc[:, PRICE_COLUMNS].copy()
    canonical["Date"] = pd.to_datetime(canonical["Date"], errors="coerce")
    canonical["Price"] = pd.to_numeric(canonical["Price"], errors="coerce")
    canonical = canonical.dropna(subset=PRICE_COLUMNS)
    canonical["Price"] = canonical["Price"].round(4)
    canonical = canonical.drop_duplicates(subset=["Date"], keep="last")
    canonical = canonical.sort_values("Date", ascending=False).reset_index(drop=True)
    canonical["Date"] = canonical["Date"].dt.strftime("%Y-%m-%d")
    return canonical


def merge_price_frames(*, existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    """Merge price frames with incoming rows winning on date overlap."""
    old = normalize_price_frame(existing).assign(_priority=0)
    new = normalize_price_frame(incoming).assign(_priority=1)
    combined = pd.concat([old, new], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    combined["Date"] = pd.to_datetime(combined["Date"])
    combined = combined.sort_values(["Date", "_priority"], ascending=[False, False])
    combined = combined.drop_duplicates(subset=["Date"], keep="first")
    combined = combined.sort_values("Date", ascending=False)
    combined["Date"] = combined["Date"].dt.strftime("%Y-%m-%d")
    return combined[PRICE_COLUMNS].reset_index(drop=True)


def load_price_csv(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        return pd.DataFrame(columns=PRICE_COLUMNS)
    return normalize_price_frame(pd.read_csv(file_path))


def save_price_csv(*, frame: pd.DataFrame, file_path: Path) -> None:
    atomic_write_csv(frame=normalize_price_frame(frame), path=file_path)


def get_forex_rate(*, currency: str, date: str, prices_folder: Path) -> float:
    """Return the as-of rate from a canonical CURRENCY_EUR price file."""
    if currency == "EUR":
        return 1.0
    path = prices_folder / f"{currency}_EUR.csv"
    frame = load_price_csv(path)
    if frame.empty:
        raise FileNotFoundError(f"No forex data for {currency}: {path}")
    dates = pd.to_datetime(frame["Date"])
    target = pd.Timestamp(date)
    eligible = frame.loc[dates <= target]
    row = eligible.iloc[0] if not eligible.empty else frame.iloc[-1]
    return float(row["Price"])


def price_on_or_before(*, symbol: str, date: str, prices_folder: Path) -> float:
    path = prices_folder / f"{symbol}.csv"
    frame = load_price_csv(path)
    if frame.empty:
        raise FileNotFoundError(path)
    dates = pd.to_datetime(frame["Date"])
    eligible = frame.loc[dates <= pd.Timestamp(date)]
    if eligible.empty:
        return float(frame.iloc[-1]["Price"])
    return float(eligible.iloc[0]["Price"])


def json_value(value: Any) -> Any:
    """Convert common pandas values to JSON-compatible values."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return value
