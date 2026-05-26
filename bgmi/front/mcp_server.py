"""MCP SSE server integrated into bgmi_http Tornado server.

Provides Model Context Protocol access to BGmi operations via SSE transport
on the same port as the existing HTTP API.

Endpoints:
    GET  /mcp/sse           - SSE stream (long-lived connection)
    POST /mcp/messages      - JSON-RPC message endpoint

Authentication: bgmi-token header, same as the admin API.
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from loguru import logger
from mcp.server.fastmcp import FastMCP
from mcp.shared.message import SessionMessage
from mcp.types import JSONRPCMessage

import tornado.web

from bgmi.config import cfg
from bgmi.lib import controllers as ctl

# ---------------------------------------------------------------------------
# MCP Server Instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "bgmi",
    instructions=(
        "BGmi is a CLI tool for subscribing to and downloading bangumi (anime). "
        "Use these tools to manage subscriptions, search for anime, check schedules, "
        "configure filters, and trigger downloads."
    ),
)


# ---------------------------------------------------------------------------
# MCP Tools - mapped from bgmi.lib.controllers
# ---------------------------------------------------------------------------


@mcp.tool()
def cal(force_update: bool = False) -> Dict[str, Any]:
    """Get the weekly bangumi calendar.

    Returns the schedule of currently updating bangumi grouped by weekday.
    """
    return ctl.cal(force_update=force_update)


@mcp.tool()
def list_subscriptions() -> Dict[str, Any]:
    """List all currently followed bangumi subscriptions."""
    return ctl.list_()


@mcp.tool()
def add(name: str, episode: Optional[int] = None) -> Dict[str, Any]:
    """Subscribe to a bangumi by name.

    Args:
        name: Name of the bangumi to subscribe to (fuzzy matched).
        episode: Starting episode number (default: 0).
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
    return ctl.mark(name=name, episode=episode)


@mcp.tool()
def download(name: str, title: str, episode: int, download_url: str) -> Dict[str, Any]:
    """Download a specific episode.

    Args:
        name: Bangumi name.
        title: Episode title.
        episode: Episode number.
        download_url: Torrent/magnet URL.
    """
    ctl.download(name=name, title=title, episode=episode, download_url=download_url)
    return {"status": "success", "message": f"Download queued: {title}"}


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
    return {"status": "info", "message": "", "data": json.loads(cfg.model_dump_json())}


@mcp.tool()
def set_status(name: str, status: int) -> Dict[str, Any]:
    """Set the follow status of a bangumi.

    Args:
        name: Name of the followed bangumi.
        status: Status code (1=followed, 2=updated, 3=deleted).
    """
    return ctl.status_(name=name, status=status)


# ---------------------------------------------------------------------------
# Tornado Handlers - SSE Transport for MCP
# ---------------------------------------------------------------------------

# Active SSE sessions: session_id -> write stream
_sessions: Dict[str, MemoryObjectSendStream[SessionMessage | Exception]] = {}


def _check_token(handler: tornado.web.RequestHandler) -> bool:
    """Validate admin token from request header."""
    token = handler.request.headers.get("bgmi-token", "")
    return token == cfg.http.admin_token


class McpSseHandler(tornado.web.RequestHandler):
    """GET /mcp/sse - Establish SSE connection for MCP protocol."""

    async def get(self) -> None:
        if not _check_token(self):
            self.set_status(401)
            self.finish({"error": "Unauthorized"})
            return

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        session_id = str(uuid.uuid4())

        # Create memory stream pair for this session
        # client_send -> server reads (incoming JSON-RPC from client)
        # server_send -> client reads (outgoing JSON-RPC to client via SSE)
        client_send, client_recv = anyio.create_memory_object_stream[SessionMessage | Exception](max_buffer_size=0)
        server_send, server_recv = anyio.create_memory_object_stream[SessionMessage](max_buffer_size=0)

        _sessions[session_id] = client_send

        # Send the endpoint event so client knows where to POST messages
        endpoint_url = f"/mcp/messages?session_id={session_id}"
        self.write(f"event: endpoint\ndata: {endpoint_url}\n\n")
        await self.flush()

        # Run MCP server session in background, forward output via SSE
        server = mcp._mcp_server
        init_options = server.create_initialization_options()

        async def run_mcp_session() -> None:
            try:
                await server.run(client_recv, server_send, init_options)
            except Exception:
                logger.exception("MCP session error")
            finally:
                _sessions.pop(session_id, None)

        async def stream_responses() -> None:
            try:
                async for message in server_recv:
                    json_data = message.message.model_dump_json(by_alias=True, exclude_none=True)
                    self.write(f"event: message\ndata: {json_data}\n\n")
                    await self.flush()
            except (asyncio.CancelledError, anyio.ClosedResourceError):
                pass
            finally:
                self.finish()

        # Run both coroutines concurrently
        session_task = asyncio.ensure_future(run_mcp_session())
        stream_task = asyncio.ensure_future(stream_responses())

        try:
            # Wait until either task finishes (connection closed or session ends)
            done, pending = await asyncio.wait(
                [session_task, stream_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
        except asyncio.CancelledError:
            session_task.cancel()
            stream_task.cancel()
        finally:
            _sessions.pop(session_id, None)
            await client_send.aclose()
            await server_send.aclose()

    def on_connection_close(self) -> None:
        """Handle client disconnect."""
        logger.debug("MCP SSE client disconnected")


class McpMessageHandler(tornado.web.RequestHandler):
    """POST /mcp/messages - Receive JSON-RPC messages for an MCP session."""

    async def post(self) -> None:
        if not _check_token(self):
            self.set_status(401)
            self.finish({"error": "Unauthorized"})
            return

        session_id = self.get_argument("session_id", None)
        if not session_id:
            self.set_status(400)
            self.finish({"error": "Missing session_id parameter"})
            return

        writer = _sessions.get(session_id)
        if not writer:
            self.set_status(404)
            self.finish({"error": "Session not found"})
            return

        try:
            body = self.request.body
            message = JSONRPCMessage.model_validate_json(body)
            session_message = SessionMessage(message)
            await writer.send(session_message)
            self.set_status(202)
            self.finish("Accepted")
        except Exception as e:
            logger.warning(f"Failed to parse MCP message: {e}")
            self.set_status(400)
            self.finish({"error": f"Invalid message: {e}"})


def get_mcp_handlers() -> List[Any]:
    """Return Tornado URL handler specs for MCP endpoints."""
    return [
        (r"^/mcp/sse$", McpSseHandler),
        (r"^/mcp/messages$", McpMessageHandler),
    ]
