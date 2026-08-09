from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pandas as pd

from portfolio_core.paths import PortfolioPaths


@contextmanager
def _atomic_path(path: Path) -> Iterator[Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        yield temporary
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_csv(*, frame: pd.DataFrame, path: Path, index: bool = False) -> None:
    """Atomically write a CSV."""
    with _atomic_path(path) as temporary:
        frame.to_csv(temporary, index=index)


def atomic_write_json(*, data: object, path: Path) -> None:
    """Atomically write indented JSON."""
    with _atomic_path(path) as temporary:
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def atomic_write_text(*, text: str, path: Path) -> None:
    """Atomically write text."""
    with _atomic_path(path) as temporary:
        temporary.write_text(text, encoding="utf-8")


@contextmanager
def mutation_session(
    *,
    paths: PortfolioPaths,
) -> Iterator[None]:
    """Prevent concurrent mutation of one workspace."""
    paths.runtime.mkdir(parents=True, exist_ok=True)
    lock_path = paths.runtime / "mutation.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"Portfolio workspace is already being mutated: {lock_path}") from exc

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
            lock_file.write(f"{os.getpid()}\n")
        yield
    finally:
        lock_path.unlink()
