# BGmi User Script Development Guide

This document provides everything needed to develop a custom BGmi script. Scripts allow you to add custom bangumi sources that BGmi doesn't natively support.

## Overview

A user script is a Python file placed in `~/.bgmi/scripts/` (or `$BGMI_SCRIPT_PATH`). It must define a class named `Script` that inherits from `bgmi.script.ScriptBase`. BGmi's `ScriptRunner` auto-discovers and loads all `*.py` files in the scripts directory.

## File Location

- **Scripts directory**: `~/.bgmi/scripts/` (configurable via `BGMI_SCRIPT_PATH` env or `script_path` in `config.toml`)
- **Hooks directory**: `~/.bgmi/hooks/` (configurable via `BGMI_HOOK_PATH` env or `hook_path` in `config.toml`)

## Script Structure

Every script file MUST export a class named exactly `Script`:

```python
import datetime
from typing import Dict

from bgmi.script import ScriptBase
from bgmi.utils import parse_episode


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = "My Custom Bangumi"  # REQUIRED: unique name
        cover = "https://example.com/cover.jpg"  # Cover image URL
        update_time = "Mon"  # One of: Sun, Mon, Tue, Wed, Thu, Fri, Sat, Unknown
        due_date = datetime.datetime(2025, 12, 31)  # Optional: auto-skip after this date

    def get_download_url(self) -> Dict[int, str]:
        """
        Fetch and return download URLs.
        Returns: {episode_number: download_url_or_magnet}
        """
        # Your custom fetching logic here
        return {
            1: "magnet:?xt=urn:btih:...",
            2: "https://example.com/ep2.torrent",
        }
```

## ScriptBase API Reference

### Inner Class: `Model`

| Field | Type | Required | Description |
|---|---|---|---|
| `bangumi_name` | `str` | **YES** | Unique identifier for this bangumi |
| `cover` | `str` | No | Cover image URL |
| `update_time` | `str` | No (default `"Unknown"`) | Weekday: `Sun`, `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Unknown` |
| `due_date` | `datetime.datetime` | No | Script is skipped after this date |

### Method: `get_download_url() -> Dict[int, str]`

**REQUIRED**. Must return a dict mapping episode numbers (int) to download URLs (str).

- Keys: episode numbers (e.g., `1`, `2`, `3`)
- Values: download URLs — can be HTTP links to `.torrent` files or magnet links
- Return empty dict `{}` if no new episodes found

### Using Built-in Data Sources

`ScriptBase` supports delegating episode fetching to BGmi's built-in data sources instead of implementing custom logic:

```python
class Script(ScriptBase):
    # Set source to use a built-in data source
    source = "mikan_project"  # Options: "mikan_project", "bangumi_moe", "dmhy"

    class Model(ScriptBase.Model):
        bangumi_name = "My Bangumi"
        update_time = "Fri"

    def get_download_url(self) -> Dict[int, str]:
        # When self.source is set, this delegates to the data source.
        # You must also set self._data with fetch parameters:
        #   bangumi_id: str
        #   subtitle_list: Optional[List[str]]
        #   max_page: int
        return super().get_download_url()
```

When `self.source` is set, calling `super().get_download_url()` will invoke `fetch_episode_of_bangumi` from the specified data source using `self._data` as parameters.

## Utility Functions

### `bgmi.utils.parse_episode(title: str) -> int`

Extracts episode number from a torrent title string. Uses the `anime_episode_parser` library.

```python
from bgmi.utils import parse_episode

episode = parse_episode("[SubGroup][Anime Name][03][1080P]")  # Returns: 3
```

## How Scripts Are Loaded

1. `ScriptRunner` scans `cfg.script_path` for `*.py` files
2. Each file is loaded via `SourceFileLoader` and `mod.Script()` is instantiated
3. `Model.due_date` is checked — expired scripts are skipped
4. Valid scripts are added to `ScriptRunner.scripts`

## How Scripts Are Executed

When `bgmi update` runs:

1. `ScriptRunner.run()` iterates over loaded scripts
2. For each script, calls `script.get_download_url()`
3. Compares returned episode numbers against `Scripts` DB table (last known episode)
4. New episodes (episode > last recorded) are queued for download
5. The `Scripts` DB record is updated with the latest episode number

## Database Model: `Scripts`

BGmi tracks script state in SQLite:

| Field | Type | Description |
|---|---|---|
| `bangumi_name` | TextField | Primary identifier (matches `Model.bangumi_name`) |
| `episode` | IntegerField | Last downloaded episode number |
| `status` | IntegerField | 0=deleted, 1=followed, 2=updated |
| `updated_time` | IntegerField | Unix timestamp of last update |

## Complete Example: Custom RSS Source

```python
import datetime
from typing import Dict

import requests
from bs4 import BeautifulSoup

from bgmi.script import ScriptBase
from bgmi.utils import parse_episode


class Script(ScriptBase):
    class Model(ScriptBase.Model):
        bangumi_name = "Frieren: Beyond Journey's End"
        cover = "https://example.com/frieren-cover.jpg"
        update_time = "Fri"
        due_date = datetime.datetime(2025, 6, 30)

    def get_download_url(self) -> Dict[int, str]:
        """Scrape a custom RSS feed for magnet links."""
        rss_url = "https://example.com/rss/frieren"
        resp = requests.get(rss_url, timeout=30)
        soup = BeautifulSoup(resp.content, "xml")

        result = {}
        for item in soup.find_all("item"):
            title = item.find("title").text
            link = item.find("link").text  # magnet or .torrent URL
            episode = parse_episode(title)
            if episode and episode not in result:
                result[episode] = link

        return result
```

## Hook System

Hooks are separate from scripts. They run pre/post download actions.

### File Location

`~/.bgmi/hooks/*.py` — each file may contain one or more classes implementing `HookBase`.

### HookBase Protocol

```python
from bgmi.script import HookBase


class MyHook(HookBase):
    def pre_add_download(self, *args, **kwargs) -> None:
        """Called before downloads are added to the queue."""
        pass

    def post_add_download(self, *args, **kwargs) -> None:
        """Called after downloads are added.

        Keyword args:
            download_queue: list of new downloads
            redownload_queue: list of re-downloads
        """
        # Example: send notification
        pass
```

### Hook Discovery

`HookRunner` scans `cfg.hook_path` for `*.py` files and inspects all module attributes. Any class that is a subclass of `HookBase` (but not `HookBase` itself) is instantiated and registered.

## Debugging

Set `DEBUG_SCRIPT=1` environment variable to print full tracebacks when scripts fail to load:

```bash
DEBUG_SCRIPT=1 bgmi update
```

## Checklist for New Scripts

- [ ] File is in `~/.bgmi/scripts/` with `.py` extension
- [ ] Exports a class named exactly `Script`
- [ ] `Script` inherits from `bgmi.script.ScriptBase`
- [ ] Inner `Model` class has `bangumi_name` set (unique, non-empty)
- [ ] `update_time` is one of: `Sun`, `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Unknown`
- [ ] `get_download_url()` returns `Dict[int, str]` (episode → URL)
- [ ] Dependencies are installed in the same Python environment as BGmi
- [ ] `due_date` set if the bangumi has a known end date
