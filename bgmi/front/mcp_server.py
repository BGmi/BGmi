"""MCP SSE server integrated into bgmi_http.

Provides Model Context Protocol access to BGmi operations via SSE transport
on the same port as the existing HTTP API.

Endpoints (mounted at /mcp):
    GET  /mcp/sse           - SSE stream (long-lived connection)
    POST /mcp/messages      - JSON-RPC message endpoint

Authentication: Bearer token in Authorization header, validated against admin_token.
"""

import json
from typing import Any, Dict, List, Optional

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp.server.fastmcp import FastMCP

from bgmi.config import cfg
from bgmi.lib import controllers as ctl
from bgmi.lib.download import download_episode, get_download_driver
from bgmi.lib.table import Download, Followed
from bgmi.website.model import Episode

mcp = FastMCP(
    "bgmi",
    instructions=(
        "BGmi is a CLI tool for subscribing to and downloading bangumi (anime). "
        "Use these tools to manage subscriptions, search for anime, check schedules, "
        "configure filters, and trigger downloads."
    ),
)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def cal(force_update: bool = False) -> Dict[str, Any]:
    """Get the weekly bangumi calendar.

    Returns the schedule of currently updating bangumi grouped by weekday.
    """
    result = ctl.cal(force_update=force_update)
    return {
        day: [{k: v for k, v in item.items() if not k.startswith("_")} for item in items]
        for day, items in result.items()
    }


@mcp.tool()
def list() -> List[Dict[str, Any]]:
    """List all currently followed bangumi subscriptions."""
    results = []
    for followed, bangumi in Followed.get_all_followed():
        info: Dict[str, Any] = {
            "name": followed.bangumi_name,
            "episode": followed.episode,
            "status": followed.status,
            "updated_time": followed.updated_time,
            "update_day": bangumi.update_day,
            "season": followed.season,
        }
        if followed.episode_offset:
            info["episode_offset"] = followed.episode_offset
        if followed.display_name:
            info["display_name"] = followed.display_name
        results.append(info)
    return results


@mcp.tool()
def add(
    name: str,
    episode: Optional[int] = None,
    season: Optional[int] = None,
    episode_offset: Optional[int] = None,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Subscribe to a bangumi by name.

    Args:
        name: Name of the bangumi to subscribe to (fuzzy matched).
        episode: Starting episode number (default: auto-detect latest).
        season: Override season number (default: auto-detect from name). Also works for already subscribed bangumi.
        episode_offset: Episode number offset for path formatter (e.g. 48 to map EP8 -> EP56).
        display_name: Override display name in path formatter (e.g. for TMDB matching).
    """
    return ctl.add(name=name, episode=episode, season=season, episode_offset=episode_offset, display_name=display_name)


@mcp.tool()
def delete(name: str) -> Dict[str, Any]:
    """Unsubscribe from a bangumi.

    Args:
        name: Name of the bangumi to unsubscribe from.
    """
    return ctl.delete(name=name)


@mcp.tool()
def search(
    keyword: str,
    count: int = 3,
    regex: Optional[str] = None,
    min_episode: Optional[int] = None,
    max_episode: Optional[int] = None,
) -> Dict[str, Any]:
    """Search for bangumi episodes by keyword.

    Args:
        keyword: Search keyword.
        count: Max number of results per episode.
        regex: Optional regex to filter results.
        min_episode: Minimum episode number filter.
        max_episode: Maximum episode number filter.
    """
    return ctl.search(
        keyword=keyword,
        count=count,
        regex=regex,
        min_episode=min_episode,
        max_episode=max_episode,
    )


@mcp.tool()
def seen_forget(name: str, episode: int) -> Dict[str, Any]:
    """Remove an episode from download records (triggers re-download on next update).

    Args:
        name: Name of the bangumi.
        episode: Episode number to forget.
    """
    try:
        followed = Followed.get(Followed.bangumi_name == name)
    except Followed.NotFoundError:
        return {"status": "error", "message": f"Bangumi {name} is not followed"}

    if episode not in followed.episodes:
        return {"status": "error", "message": f"Episode {episode} is not in download records"}

    followed.episodes.remove(episode)
    followed.save()

    reset_count = (
        Download.update({Download.status: Download.STATUS_NOT_DOWNLOAD, Download.task_id: None})
        .where(Download.bangumi_name == name, Download.episode == episode)
        .execute()
    )

    return {
        "status": "success",
        "message": f"Forgot episode {episode} of {name} (reset {reset_count} download records), will re-download on next update",
    }


@mcp.tool()
def update(names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Trigger bangumi update: check for new episodes and download them.

    This is the main way to fetch new episodes for subscribed bangumi.

    Args:
        names: Optional list of bangumi names to update. If empty/None, updates all subscriptions.
    """
    from bgmi.lib.postprocessor import process_completed_downloads

    ctl.update(names=names or [], download=True, not_ignore=False)

    if cfg.enable_path_formatter:
        process_completed_downloads()

    return {
        "status": "success",
        "message": f"Update completed for: {', '.join(names) if names else 'all subscriptions'}",
    }


@mcp.tool()
def download(name: str, title: str, episode: int, download_url: str) -> Dict[str, Any]:
    """Manually download a specific episode by providing a torrent/magnet URL.

    NOTE: This is for manual downloads only. To trigger automatic updates
    and download new episodes, use the 'update' tool instead.

    Args:
        name: Bangumi name.
        title: Episode title.
        episode: Episode number.
        download_url: Torrent/magnet URL.
    """
    e = Episode(name=name, title=title, episode=episode, download=download_url)
    success = download_episode(e)
    if success:
        return {"status": "success", "message": f"Download queued: {title}"}
    return {"status": "error", "message": f"Failed to download: {title}"}


@mcp.tool()
def get_filter(name: str) -> Dict[str, Any]:
    """Get the download filter settings for a bangumi.

    Args:
        name: Name of the followed bangumi.
    """
    return ctl.filter_(name=name)


@mcp.tool()
def set_filter(
    name: str,
    subtitle: Optional[str] = None,
    include: Optional[str] = None,
    exclude: Optional[str] = None,
    regex: Optional[str] = None,
) -> Dict[str, Any]:
    """Set download filter for a bangumi.

    Args:
        name: Name of the followed bangumi.
        subtitle: Comma-separated subtitle group names to include.
        include: Comma-separated keywords that must appear in title.
        exclude: Comma-separated keywords that must NOT appear in title.
        regex: Regex pattern for title filtering.
    """
    return ctl.filter_(
        name=name,
        subtitle=subtitle,
        include=include,
        exclude=exclude,
        regex=regex,
    )


@mcp.tool()
def postprocess() -> Dict[str, Any]:
    """Process completed downloads: move files to formatted paths and remove torrents.

    Checks all active download tasks, moves completed ones to the path formatter
    destination, cleans up temp directories, and removes torrents from the downloader.
    """
    from bgmi.lib.postprocessor import process_completed_downloads

    if not cfg.enable_path_formatter:
        return {"status": "skipped", "message": "path formatter is disabled"}

    process_completed_downloads()
    return {"status": "success", "message": "Post-processing completed"}


@mcp.tool()
def download_status() -> List[Dict[str, Any]]:
    """Get download progress for all active tasks.

    Returns a list of downloads with their current status from the downloader.
    """
    downloads = Download.get_all_downloads(status=Download.STATUS_DOWNLOADING)
    if not downloads:
        return []

    driver = get_download_driver(cfg.download_delegate)
    results = []
    for dl in downloads:
        info: Dict[str, Any] = {
            "name": dl.bangumi_name,
            "title": dl.title,
            "episode": dl.episode,
            "task_id": dl.task_id,
        }
        if dl.task_id:
            try:
                status = driver.get_status(dl.task_id)
                info["status"] = status.name
            except Exception:
                info["status"] = "unknown"
        else:
            info["status"] = "no_task_id"
        results.append(info)
    return results


@mcp.tool()
def get_config() -> Dict[str, Any]:
    """Get the current BGmi configuration."""
    result: Dict[str, Any] = json.loads(cfg.model_dump_json())
    return result


@mcp.tool()
def set_status(name: str, status: int) -> Dict[str, Any]:
    """Set the follow status of a bangumi.

    Args:
        name: Name of the followed bangumi.
        status: Status code (1=followed, 2=updated, 0=deleted).
    """
    try:
        followed = Followed.get(Followed.bangumi_name == name)
    except Followed.NotFoundError:
        return {"status": "error", "message": f"Bangumi {name} is not followed"}

    followed.status = status
    followed.save()
    return {"status": "success", "message": f"Set {name} status to {status}"}


# ---------------------------------------------------------------------------
# Auth Middleware
# ---------------------------------------------------------------------------


class TokenAuthMiddleware:
    """ASGI middleware that validates Bearer token against admin_token."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if token != cfg.http.admin_token:
            response = Response("Unauthorized", status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------


def create_mcp_app() -> Starlette:
    """Create the MCP SSE sub-application with auth middleware."""
    sse_app = mcp.sse_app()
    return Starlette(
        routes=sse_app.routes,
        middleware=[Middleware(TokenAuthMiddleware)],
    )
