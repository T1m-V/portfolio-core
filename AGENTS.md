# AGENTS.md

## Purpose

`portfolio-core` is the dependency-free foundation for the portfolio projects. It owns shared
configuration, data-workspace paths, persisted-data schema checks, metadata loading, and canonical
price-history utilities. It must not import another `portfolio-*` package.

## Repository Role

| Repository | Relationship to this package |
| --- | --- |
| `portfolio-market-data` | Direct consumer of settings, paths, metadata, and price utilities. |
| `portfolio-crypto-data` | Direct consumer of settings, paths, metadata, and forex/price utilities. |
| `portfolio-dashboard` | Direct consumer of settings, paths, metadata, schema validation, and forex utilities. |
| `portfolio-data` | Supplies the external filesystem workspace. Its lockfile pins this package because it is a transitive dependency of both loaders. |

Dependency direction is one-way: core -> loaders -> dashboard. Keep application code, network
clients, FastAPI code, and React code out of this repository.

## Main Interfaces

- `portfolio_core.settings`
  - resolves an explicit directory, `PORTFOLIO_DATA_DIR`, or persisted user configuration;
  - loads `.env` from the selected data workspace when an application opts in;
  - persists the chosen data directory for the dashboard CLI.
- `portfolio_core.context`
  - combines settings and paths at an explicit application boundary;
  - provides task-local activation for a single synchronous call tree, never a process-global
    data root.
- `portfolio_core.paths`
  - defines the one authoritative external workspace layout;
  - exposes immutable paths rooted in a caller-supplied directory.
- `portfolio_core.schema`
  - validates `portfolio.toml` and `schema_version`.
- `portfolio_core.price_history`
  - normalizes, merges, reads, and writes canonical price history;
  - provides as-of price and forex lookup.
- `portfolio_core.workspace`
  - serializes loader mutations with a workspace lock;
  - provides atomic file replacement.

The data workspace is runtime state. Never infer a data path from a source checkout.

## Refactoring Policy

- Favor the cleanest current interface over backward compatibility.
- Treat implementation details as private unless they are re-exported intentionally from
  `portfolio_core.__init__` or documented as a persisted-data contract.
- Change signatures and remove obsolete helpers freely when the change improves the design.
- Update every downstream repository in the same refactor instead of adding deprecated aliases,
  old module namespaces, argument adapters, or duplicate implementations.
- Do not add compatibility shims unless the user explicitly asks for a staged migration.
- Prefer a one-time data migration and schema-version bump over supporting two directory or file
  layouts indefinitely.
- Keep one owner for every shared rule. If logic is useful to multiple packages, put it here and
  delete downstream copies.

The intentionally coordinated contracts are the workspace layout, `portfolio.toml`, price CSV
shape (`Date`, `Price`, descending by date), and `latest_prices.csv` shape
(`date, isin, price`). They may still change, but all readers, writers, tests, tags, and migration
instructions must change together.

## Release Coordination

For a core change:

1. Update the version and tests here.
2. Build and tag the new core release.
3. Update the core requirement and Git tag in `portfolio-market-data` and
   `portfolio-crypto-data`.
4. Release those packages when their locks change.
5. Update `portfolio-dashboard` and `portfolio-data` to the resulting tags and regenerate their
   `uv.lock` files.

Never move an existing release tag. Use a new version once a tag has been published.

## Development

```powershell
uv sync
uv run ruff check src tests
uv run python -m pytest
uv build
```

Python is pinned to 3.14. uv stores the actual environment in its centralized cache; a local
`.venv` entry may only be a junction to that cache.

## Safety

- Do not read or print credentials while testing settings behavior.
- Use temporary directories for path and schema tests.
- Do not mutate the real portfolio data workspace from unit tests.
- Keep the mutation lock under `runtime/`; never invent package-specific lock files.
- Preserve unrelated user changes and do not commit build artifacts from `dist/`.
