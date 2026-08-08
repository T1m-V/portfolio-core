# portfolio-core

Shared path, metadata, price-history, and workspace-schema behavior for the portfolio projects.

```powershell
uv sync
uv run pytest
```

Create a `PortfolioContext` at an application boundary and pass its `paths` explicitly to
operations:

```python
from portfolio_core import PortfolioContext

context = PortfolioContext.load("C:/portfolio-data")
price_path = context.paths.direct_price("USD_EUR")
```

`PORTFOLIO_DATA_DIR` and `save_data_directory(...)` remain CLI conveniences. Package modules do
not retain a process-global workspace or infer data paths from source checkouts.
