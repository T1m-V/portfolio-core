from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from portfolio_core import (
    PortfolioPaths,
    atomic_write_csv,
    atomic_write_json,
    atomic_write_text,
    mutation_session,
)


def test_atomic_writers_create_complete_files(tmp_path: Path) -> None:
    text_path = tmp_path / "nested" / "value.txt"
    json_path = tmp_path / "value.json"
    csv_path = tmp_path / "value.csv"

    atomic_write_text(text="hello", path=text_path)
    atomic_write_json(data={"answer": 42}, path=json_path)
    atomic_write_csv(frame=pd.DataFrame({"value": [1]}), path=csv_path)

    assert text_path.read_text(encoding="utf-8") == "hello"
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"answer": 42}
    assert pd.read_csv(csv_path).to_dict("records") == [{"value": 1}]
    assert not list(tmp_path.rglob("*.tmp"))


def test_atomic_writer_cleans_up_after_a_failed_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame()

    def fail(*_args, **_kwargs) -> None:
        raise OSError

    monkeypatch.setattr(frame, "to_csv", fail)

    with pytest.raises(OSError):
        atomic_write_csv(frame=frame, path=tmp_path / "value.csv")
    assert not list(tmp_path.iterdir())


def test_mutation_session_serializes_and_always_releases_the_lock(tmp_path: Path) -> None:
    paths = PortfolioPaths(root=tmp_path)
    lock = paths.runtime / "mutation.lock"

    with mutation_session(paths=paths):
        assert lock.read_text(encoding="utf-8").strip().isdigit()
        with pytest.raises(RuntimeError, match="already being mutated"):
            with mutation_session(paths=paths):
                pass
    assert not lock.exists()

    with pytest.raises(ValueError):
        with mutation_session(paths=paths):
            raise ValueError
    assert not lock.exists()
