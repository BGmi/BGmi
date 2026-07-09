"""MCP SSE server integrated into bgmi_http.

Provides Model Context Protocol access to BGmi operations via SSE transport
on the same port as the existing HTTP API.

Endpoints (mounted at /mcp):
    POST /mcp               - Streamable HTTP transport (Codex)
    GET  /mcp/sse           - SSE stream (long-lived connection)
    POST /mcp/messages      - JSON-RPC message endpoint

Authentication: Bearer token in Authorization header, validated against admin_token.
"""

import datetime
from typing import Any, Dict, List, Literal, Optional

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.routing import Route
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

_streamable_app: Optional[Starlette] = None


def _get_streamable_app() -> Starlette:
    global _streamable_app
    if _streamable_app is None:
        _streamable_app = mcp.streamable_http_app()
    return _streamable_app


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


FOLLOWED_STATUS = {
    Followed.STATUS_DELETED: "STATUS_DELETED",
    Followed.STATUS_FOLLOWED: "STATUS_FOLLOWED",
    Followed.STATUS_UPDATED: "STATUS_UPDATED_TODAY",
    Followed.STATUS_END: "STATUS_END_UNUSED",
}
SETTABLE_FOLLOWED_STATUS = {
    "STATUS_FOLLOWED": Followed.STATUS_FOLLOWED,
    "STATUS_UPDATED_TODAY": Followed.STATUS_UPDATED,
}
SettableFollowedStatus = Literal["STATUS_FOLLOWED", "STATUS_UPDATED_TODAY"]


def _followed_status(status: Optional[int]) -> str:
    if status is None:
        return "STATUS_NOT_FOLLOWED"
    return FOLLOWED_STATUS.get(status, f"STATUS_UNKNOWN_{status}")


def _format_timestamp(timestamp: int) -> Optional[str]:
    if not timestamp:
        return None
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).astimezone().isoformat(timespec="seconds")


@mcp.tool()
def cal(force_update: bool = False) -> Dict[str, Any]:
    """Get the current-season bangumi calendar grouped by weekday.

    This is the seasonal/quarterly bangumi calendar, not just the user's
    subscriptions. Use list() when you only need followed subscriptions.

    Status values:
        STATUS_NOT_FOLLOWED: In calendar but not subscribed.
        STATUS_FOLLOWED: Subscribed.
        STATUS_UPDATED_TODAY: Subscribed and successfully updated today.
        STATUS_DELETED: In calendar and previously unsubscribed by the user.
    """
    result = ctl.cal(force_update=force_update)
    calendar: Dict[str, List[Dict[str, Any]]] = {}
    for day, items in result.items():
        calendar[day] = []
        for item in items:
            data = {k: v for k, v in item.items() if not k.startswith("_")}
            if "status" in data:
                data["status"] = _followed_status(data["status"])
            calendar[day].append(data)
    return calendar


@mcp.tool()
def list() -> List[Dict[str, Any]]:
    """List all currently followed bangumi subscriptions.

    Status values:
        STATUS_FOLLOWED: Subscribed.
        STATUS_UPDATED_TODAY: Subscribed and successfully updated today. It automatically
            returns to STATUS_FOLLOWED after today.
    """
    results = []
    for followed, bangumi in Followed.get_all_followed():
        info: Dict[str, Any] = {
            "name": followed.bangumi_name,
            "episode": followed.episode,
            "status": _followed_status(followed.status),
            "updated_at": _format_timestamp(followed.updated_time),
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
    episode: Optional[int] = 0,
    season: Optional[int] = None,
    episode_offset: Optional[int] = None,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Subscribe to a bangumi by name.

    Args:
        name: Name of the bangumi to subscribe to (fuzzy matched).
        episode: Mark episodes 1..N as already downloaded. Default 0 starts downloading from episode 1.
            Use null to mark currently available episodes as already downloaded.
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
def seen(name: str) -> Dict[str, Any]:
    """Get downloaded episode records for a followed bangumi.

    Args:
        name: Name of the bangumi.
    """
    return ctl.seen(name)


@mcp.tool()
def seen_forget(name: str, episode: int) -> Dict[str, Any]:
    """Remove an episode from download records (triggers re-download on next update).

    Args:
        name: Name of the bangumi.
        episode: Episode number to forget.
    """
    return ctl.seen_forget(name, episode)


@mcp.tool()
def seen_mark(name: str, episode: int) -> Dict[str, Any]:
    """Add an episode to download records (marks it as seen).

    Args:
        name: Name of the bangumi.
        episode: Episode number to mark as seen.
    """
    return ctl.seen_mark(name, episode)


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
    subtitle: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    regex: Optional[str] = None,
) -> Dict[str, Any]:
    """Set download filter for a bangumi.

    Args:
        name: Name of the followed bangumi.
        subtitle: Subtitle group names to include. Empty list clears selected subtitle groups.
        include: Keywords that must appear in title. Empty list clears include keywords.
        exclude: Keywords that must NOT appear in title. Empty list clears exclude keywords.
        regex: Regex pattern for title filtering.
    """
    return ctl.filter_(
        name=name,
        subtitle=",".join(subtitle) if subtitle is not None else None,
        include=",".join(include) if include is not None else None,
        exclude=",".join(exclude) if exclude is not None else None,
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
def download_status(limit: int = 20) -> List[Dict[str, Any]]:
    """Get download progress for all active tasks.

    Returns the newest active download tasks first.

    Args:
        limit: Maximum number of tasks to return. Use a small number to avoid noisy old records.
    """
    limit = max(1, min(limit, 100))
    downloads = Download.get_all_downloads(status=Download.STATUS_DOWNLOADING)
    if not downloads:
        return []

    driver = get_download_driver(cfg.download_delegate)
    results = []
    for dl in sorted(downloads, key=lambda item: item.id, reverse=True)[:limit]:
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
def set_status(name: str, status: SettableFollowedStatus) -> Dict[str, Any]:
    """Set the follow lifecycle status of a bangumi.

    This is a repair/debug tool for follow lifecycle state. Prefer delete() for
    unsubscribe operations. Finished/old bangumi are managed by Bangumi.status
    through the calendar lifecycle, not by this follow status.

    Args:
        name: Name of the followed bangumi.
        status: STATUS_FOLLOWED means subscribed. STATUS_UPDATED_TODAY means
            subscribed and successfully updated today; it normally comes from
            update() and automatically returns to STATUS_FOLLOWED after today.
    """
    parsed_status = SETTABLE_FOLLOWED_STATUS.get(status)
    if parsed_status is None:
        allowed = ", ".join(SETTABLE_FOLLOWED_STATUS)
        return {"status": "error", "message": f"Invalid follow status {status!r}. Use one of: {allowed}"}

    try:
        followed = Followed.get(Followed.bangumi_name == name)
    except Followed.NotFoundError:
        return {"status": "error", "message": f"Bangumi {name} is not followed"}

    followed.status = parsed_status
    if parsed_status == Followed.STATUS_UPDATED:
        followed.updated_time = int(datetime.datetime.now().timestamp())
    followed.save()
    follow_status = _followed_status(followed.status)
    return {
        "status": "success",
        "message": f"Set {name} follow status to {follow_status}",
        "follow_status": follow_status,
    }


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
    """Create the MCP sub-application with Streamable HTTP and SSE transports."""
    sse_app = mcp.sse_app()
    streamable_app = _get_streamable_app()
    streamable_route = next(route for route in streamable_app.routes if getattr(route, "path", None) == "/mcp")

    return Starlette(
        routes=[
            Route(
                "/",
                endpoint=streamable_route.endpoint,  # type: ignore[attr-defined]
                methods=streamable_route.methods,  # type: ignore[attr-defined]
                name=getattr(streamable_route, "name", None),
            ),
            *sse_app.routes,
        ],
        middleware=[Middleware(TokenAuthMiddleware)],
        lifespan=streamable_app.router.lifespan_context,
    )


def create_mcp_streamable_route(path: str = "/mcp") -> Route:
    """Create the top-level Streamable HTTP route without Starlette's slash redirect."""
    streamable_app = _get_streamable_app()
    streamable_route = next(route for route in streamable_app.routes if getattr(route, "path", None) == "/mcp")
    return Route(
        path,
        endpoint=TokenAuthMiddleware(streamable_route.endpoint),  # type: ignore[attr-defined]
        methods=streamable_route.methods,  # type: ignore[attr-defined]
        name=getattr(streamable_route, "name", None),
    )
