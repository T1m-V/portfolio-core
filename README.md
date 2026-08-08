# portfolio-core

Shared path, metadata, price-history, and workspace-schema behavior for the portfolio projects.

```powershell
uv sync
uv run pytest
```

Set `PORTFOLIO_DATA_DIR` or call `save_data_directory(...)` once to select the external data
workspace. Source checkouts are never used as data locations.
