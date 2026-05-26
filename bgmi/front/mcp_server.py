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
from bgmi.lib.download import download_episode
from bgmi.lib.table import Followed
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
    return ctl.cal(force_update=force_update)


@mcp.tool()
def list_subscriptions() -> List[Dict[str, Any]]:
    """List all currently followed bangumi subscriptions."""
    results = []
    for followed, bangumi in Followed.get_all_followed():
        results.append(
            {
                "name": followed.bangumi_name,
                "episode": followed.episode,
                "status": followed.status,
                "updated_time": followed.updated_time,
                "update_day": bangumi.update_day,
            }
        )
    return results


@mcp.tool()
def add(name: str, episode: Optional[int] = None) -> Dict[str, Any]:
    """Subscribe to a bangumi by name.

    Args:
        name: Name of the bangumi to subscribe to (fuzzy matched).
        episode: Starting episode number (default: auto-detect latest).
    """
    return ctl.add(name=name, episode=episode)


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
def mark(name: str, episode: int) -> Dict[str, Any]:
    """Mark a bangumi as watched up to a specific episode.

    Args:
        name: Name of the bangumi.
        episode: Episode number to mark as watched.
    """
    try:
        followed = Followed.get(Followed.bangumi_name == name)
    except Followed.NotFoundError:
        return {"status": "error", "message": f"Bangumi {name} is not followed"}

    followed.episodes = set(range(episode + 1))
    followed.save()
    return {"status": "success", "message": f"Marked {name} up to episode {episode}"}


@mcp.tool()
def download(name: str, title: str, episode: int, download_url: str) -> Dict[str, Any]:
    """Download a specific episode.

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

    # Wrap with token auth middleware
    sse_app.middleware_stack = None  # force rebuild
    sse_app.user_middleware = [Middleware(TokenAuthMiddleware)] + list(sse_app.user_middleware)
    sse_app = Starlette(
        routes=sse_app.routes,
        middleware=[Middleware(TokenAuthMiddleware)],
    )

    return sse_app
