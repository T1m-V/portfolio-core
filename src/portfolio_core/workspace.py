from __future__ import annotations

import json
import os
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from portfolio_core.paths import PortfolioPaths


class WorkspaceLockedError(RuntimeError):
    """Raised when another process owns the portfolio workspace mutation lock."""


def atomic_write_csv(*, frame: pd.DataFrame, path: Path, index: bool = False) -> None:
    """Write a CSV through a same-directory temporary file and atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        frame.to_csv(temporary, index=index)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(*, data: object, path: Path) -> None:
    """Write JSON through a same-directory temporary file and atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_text(*, text: str, path: Path) -> None:
    """Write text through a same-directory temporary file and atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def mutation_session(
    *,
    paths: PortfolioPaths,
    component: str,
    version: str,
) -> Iterator[None]:
    """Serialize workspace mutations and record the latest component run."""
    paths.runtime.mkdir(parents=True, exist_ok=True)
    lock_path = paths.runtime / "mutation.lock"
    manifest_path = paths.runtime / "manifests" / f"{component}.json"
    lock_id = uuid4().hex
    lock_data = {
        "id": lock_id,
        "component": component,
        "version": version,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "started_at": _timestamp(),
    }
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        try:
            owner = lock_path.read_text(encoding="utf-8").strip()
        except OSError:
            owner = "unreadable lock"
        raise WorkspaceLockedError(
            f"Portfolio workspace is already being mutated: {lock_path} ({owner})"
        ) from exc

    with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
        json.dump(lock_data, lock_file)
        lock_file.write("\n")

    manifest = {**lock_data, "status": "running"}
    atomic_write_json(data=manifest, path=manifest_path)
    try:
        yield
    except BaseException as exc:
        atomic_write_json(
            data={
                **manifest,
                "status": "failed",
                "finished_at": _timestamp(),
                "error": f"{type(exc).__name__}: {exc}",
            },
            path=manifest_path,
        )
        raise
    else:
        atomic_write_json(
            data={**manifest, "status": "completed", "finished_at": _timestamp()},
            path=manifest_path,
        )
    finally:
        try:
            current = json.loads(lock_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            current = {}
        if current.get("id") == lock_id:
            lock_path.unlink()
