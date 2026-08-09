# portfolio-core

Shared path, metadata, price-history, and workspace-schema behavior for the portfolio projects.

## End-user installation

End users normally do not install this package directly. The market, crypto, and dashboard wheels
pin an immutable Git tag and install it into their own uv-managed environments. No core checkout is
needed.

## Developer setup

Keep the four source repositories as siblings outside OneDrive:

```text
C:\Users\timvo\source\portfolio\
|-- portfolio-core\
|-- portfolio-market-data\
|-- portfolio-crypto-data\
`-- portfolio-dashboard\
```

Then synchronize and test core directly:

```powershell
cd C:\Users\timvo\source\portfolio\portfolio-core
uv sync --frozen
uv run ruff check src tests
uv run python -m pytest
uv build
```

uv places the actual environment in its centralized cache. The local `.venv` entry is only a
junction and may be deleted and recreated with `uv sync` if necessary.

Create a `PortfolioContext` at an application boundary and pass its `paths` explicitly to
operations:

```python
from portfolio_core import PortfolioContext

context = PortfolioContext.load("C:/portfolio-data")
price_path = context.paths.direct_price("USD_EUR")
```

`PortfolioContext.load()` resolves an explicit path, `PORTFOLIO_DATA_DIR`, or the path saved by
`save_data_directory(...)`. It fails when none is configured; package modules never infer a data
path from a source checkout.
