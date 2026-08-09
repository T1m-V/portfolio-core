from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from portfolio_core.paths import PortfolioPaths
from portfolio_core.settings import resolve_data_directory

_ACTIVE_CONTEXT: ContextVar[PortfolioContext | None] = ContextVar(
    "portfolio_context",
    default=None,
)


@dataclass(frozen=True, slots=True)
class PortfolioContext:
    """Explicit runtime context passed across application boundaries."""

    paths: PortfolioPaths

    @classmethod
    def load(
        cls,
        data_dir: str | Path | None = None,
        *,
        load_secrets: bool = True,
    ) -> PortfolioContext:
        root = resolve_data_directory(data_dir)
        if load_secrets:
            load_dotenv(root / ".env", override=False)
        return cls(paths=PortfolioPaths(root=root))

    @classmethod
    def from_root(cls, root: str | Path, *, load_secrets: bool = True) -> PortfolioContext:
        return cls.load(root, load_secrets=load_secrets)

    def stock_metadata(self) -> dict[str, dict[str, Any]]:
        return _load_metadata(self.paths.stock_metadata)

    def currency_metadata(self) -> dict[str, dict[str, Any]]:
        return _load_metadata(self.paths.currency_metadata)

    def getquin_token(self) -> str:
        token = os.environ.get("GETQUIN_TOKEN", "").strip()
        if not token:
            raise RuntimeError("GETQUIN_TOKEN is not configured in the environment or data .env")
        return token

    @contextmanager
    def activate(self) -> Iterator[PortfolioContext]:
        """Make this context available to internal pipeline functions for one call tree."""
        token = _ACTIVE_CONTEXT.set(self)
        try:
            yield self
        finally:
            _ACTIVE_CONTEXT.reset(token)


def active_context() -> PortfolioContext:
    """Return the explicitly activated context or fail at the missing boundary."""
    context = _ACTIVE_CONTEXT.get()
    if context is None:
        raise RuntimeError("No PortfolioContext is active")
    return context


def _load_metadata(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
