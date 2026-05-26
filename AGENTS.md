# AGENTS.md

## Project Overview

BGmi is a Python CLI tool for subscribing to and downloading bangumi (anime). It scrapes episode info from multiple data sources and delegates downloads to various torrent clients. It also provides a web UI for management.

- **Language**: Python 3.10+
- **Package Manager**: uv (lockfile: `uv.lock`)
- **Build System**: flit-core (`pyproject.toml`)
- **Entry Points**: `bgmi` (CLI via `bgmi.main:main`), `bgmi_http` (Web server via `bgmi.front.server:main`)

## Repository Structure

```
bgmi/                  # Main package
  config.py            # Pydantic-based config, TOML read/write
  main.py              # Click CLI entry point, all subcommands
  session.py           # HTTP session management
  setup.py             # Initialization (dirs, DB, crontab)
  script.py            # User script/hook runner
  namespace.py         # Shared namespace definitions
  lib/                 # Core business logic
    controllers.py     # CLI controller layer
    models.py          # Peewee ORM models (Bangumi, Followed, Filter, Subtitle, etc.)
    download.py        # Download task preparation
    update.py          # Database update logic
    fetch.py           # Data source dispatcher
    constants.py       # Shared constants
  website/             # Data source scrapers
    base.py            # BaseWebsite abstract class
    model.py           # Episode, WebsiteBangumi data models
    bangumi_moe.py     # bangumi.moe scraper
    mikan.py           # mikanani.me scraper
    share_dmhy.py      # share.dmhy.org scraper
  downloader/          # Torrent client integrations (stevedore plugin system)
    aria2_rpc.py       # aria2 JSON-RPC
    transmission.py    # transmission-rpc
    deluge.py          # deluge-rpc
    qbittorrent.py     # qbittorrent-webapi
  front/               # Web UI backend (Tornado)
    server.py          # Tornado HTTP server
    admin.py           # Admin API handlers
    index.py           # Index/page handlers
    resources.py       # Static resource handlers
    base.py            # Base handler class
  plugin/              # Plugin subsystem
    download.py        # Download plugin interface
  utils/               # Utility functions (color output, terminal helpers)
tests/                 # pytest test suite
  conftest.py          # Fixtures, session setup, requests caching
  downloader/          # Downloader-specific tests
docs/                  # Additional documentation
images/                # README screenshots
.github/workflows/     # CI: build, lint, test, test-downloader, release
```

## Key Libraries & Frameworks

| Library | Purpose |
|---|---|
| **click** | CLI framework — all commands defined in `bgmi/main.py` |
| **pydantic** | Config validation (`bgmi/config.py`), data models |
| **peewee** | SQLite ORM — models in `bgmi/lib/models.py` |
| **tornado** | Web server for the frontend API |
| **tomlkit** | Config file read/write (preserves formatting) |
| **stevedore** | Plugin loading for downloaders (`project.entry-points."bgmi.downloader"`) |
| **beautifulsoup4** | HTML parsing in website scrapers |
| **requests** | HTTP client |
| **loguru** | Structured logging |

## Development Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with request caching (for offline/faster re-runs)
uv run pytest --cache-requests

# Type checking
uv run mypy bgmi

# Lint (via pre-commit or directly)
uv run ruff check bgmi
uv run black --check bgmi

# Release bump (Taskfile)
task bump
```

## Code Style & Conventions

- **Formatter**: Black (line length not explicitly set — uses default 88)
- **Linter**: Ruff + pre-commit hooks
- **Type Checking**: mypy with `disallow_untyped_defs = true` (relaxed for `downloader/*` and some `website/*` modules)
- **Import Order**: isort config in `pyproject.toml` (line length 120, trailing commas)
- **Max Line Length**: 120 (pylint/isort), 88 (Black default)
- **Line Endings**: LF (enforced via pre-commit, except `.vbs` files)
- **Config Model Pattern**: All configuration uses Pydantic `BaseModel` subclasses with TOML serialization
- **ORM Pattern**: Peewee models with explicit `Meta` classes, SQLite backend
- **Plugin Pattern**: Downloaders are registered as stevedore entry points in `pyproject.toml`

## Architecture Notes

- **Data Source Extensibility**: Implement `bgmi.website.base.BaseWebsite` with `search_by_keyword`, `fetch_bangumi_calendar`, `fetch_episode_of_bangumi`, `fetch_single_bangumi`.
- **Downloader Extensibility**: Implement download class and register as a `bgmi.downloader` entry point.
- **User Scripts/Hooks**: Placed in `BGMI_PATH/hooks/`, extending `bgmi.script.HookBase` with `pre_add_download` / `post_add_download`.
- **Config Path**: `~/.bgmi/config.toml` (overridable via `BGMI_PATH` env var).
- **Database**: SQLite, stored under `BGMI_PATH`.

### Built-in HTTP Server (`bgmi_http`)

Tornado-based web server providing a management API and optional static file serving for the frontend UI.

- **Entry point**: `bgmi.front.server:main` → listens on `0.0.0.0:8888` by default
- **Authentication**: Token-based via `bgmi-token` HTTP header, validated against `cfg.http.admin_token`. Unauthenticated access allowed only for `cal` and `auth` endpoints.

**Route map**:

| Route | Handler | Purpose |
|---|---|---|
| `GET /api/index` | `BangumiListHandler` | List followed bangumi (updating) with player info |
| `GET /api/old` | `BangumiListHandler` | List followed bangumi (ended) |
| `GET /api/cal` | `AdminApiHandler` | Get weekly calendar data |
| `GET /api/config` | `AdminApiHandler` | Dump current config |
| `POST /api/{action}` | `AdminApiHandler` | Mutating actions: add, delete, search, download, mark, status, filter |
| `POST /api/auth` | `AdminApiHandler` | Token verification |
| `GET /api/update` | `UpdateHandler` | Trigger bangumi update (async, with thread pool) |
| `GET /resource/feed.xml` | `RssHandler` | RSS feed of downloads |
| `GET /resource/calendar.ics` | `CalendarHandler` | ICS calendar (weekly schedule / download log) |
| `GET /bangumi/...` | Static / `BangumiHandler` | Serve downloaded episode files |
| `GET /...` | Static / `IndexHandler` | Serve frontend SPA (requires `bgmi install`) |

- **Static file mode** (`cfg.http.serve_static_files`): When enabled, Tornado directly serves the frontend SPA and bangumi files. When disabled, handlers return instructions to configure an external web server (nginx).
- **Response format**: All API responses are JSON with standard envelope: `{version, latest_version, frontend_version, status, lang, danmaku_api, data}`.
- **Frontend**: Separate project [BGmi-frontend](https://github.com/BGmi/BGmi-frontend), installed via `bgmi install` into `cfg.front_static_path`.

## Testing

- Framework: **pytest** with verbose output and duration reporting
- Coverage: tracked via `coverage` + Codecov
- Fixtures in `tests/conftest.py` handle temp dirs, mock config, and example scripts
- Downloader tests are isolated in `tests/downloader/` with their own conftest
- CI runs tests across multiple Python versions via GitHub Actions
