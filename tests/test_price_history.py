from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from portfolio_core import (
    get_forex_rate,
    load_price_csv,
    merge_price_frames,
    normalize_price_frame,
    save_price_csv,
)


def test_normalize_price_frame_cleans_and_canonicalizes_rows() -> None:
    frame = pd.DataFrame(
        {
            "Date": ["2026-01-01", "invalid", "2026-01-03", "2026-01-01"],
            "Price": [1.23456, 2, 3.33333, 1.5],
            "ignored": [1, 2, 3, 4],
        }
    )

    assert normalize_price_frame(frame).to_dict("records") == [
        {"Date": "2026-01-03", "Price": 3.3333},
        {"Date": "2026-01-01", "Price": 1.5},
    ]


def test_merge_price_frames_gives_incoming_rows_precedence() -> None:
    existing = pd.DataFrame({"Date": ["2026-01-02", "2026-01-01"], "Price": [2, 1]})
    incoming = pd.DataFrame({"Date": ["2026-01-03", "2026-01-02"], "Price": [3, 2.5]})

    assert merge_price_frames(existing=existing, incoming=incoming).to_dict("records") == [
        {"Date": "2026-01-03", "Price": 3.0},
        {"Date": "2026-01-02", "Price": 2.5},
        {"Date": "2026-01-01", "Price": 1.0},
    ]


def test_price_files_are_normalized_on_write_and_read(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "BTC.csv"
    assert load_price_csv(path).empty

    save_price_csv(
        file_path=path,
        frame=pd.DataFrame({"Date": ["2026-01-01"], "Price": [1.23456]}),
    )

    assert load_price_csv(path).to_dict("records") == [
        {"Date": "2026-01-01", "Price": 1.2346}
    ]


@pytest.mark.parametrize(
    ("currency", "date", "expected"),
    [
        ("EUR", "1900-01-01", 1.0),
        ("USD", "2026-01-04", 3.0),
        ("USD", "2026-01-02", 1.0),
        ("USD", "2025-01-01", 1.0),
        ("USD", pd.Timestamp("2026-01-03 12:00"), 3.0),
    ],
)
def test_forex_rate_uses_the_latest_available_date(
    tmp_path: Path,
    currency: str,
    date: str | pd.Timestamp,
    expected: float,
) -> None:
    save_price_csv(
        file_path=tmp_path / "USD_EUR.csv",
        frame=pd.DataFrame({"Date": ["2026-01-03", "2026-01-01"], "Price": [3, 1]}),
    )

    assert get_forex_rate(currency=currency, date=date, prices_folder=tmp_path) == expected
