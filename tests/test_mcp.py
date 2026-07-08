"""Tests for the MCP server tools and auth middleware."""

import pytest
from starlette.testclient import TestClient

from bgmi.config import cfg
from bgmi.front import mcp_server
from bgmi.front.server import make_app
from bgmi.lib.table import Followed

client = TestClient(make_app(debug=True))
headers = {"authorization": f"Bearer {cfg.http.admin_token}"}

bangumi_1 = "名侦探柯南"


@pytest.mark.usefixtures("_ensure_data")
class TestMcpAuth:
    def test_streamable_http_no_auth(self):
        r = client.post("/mcp")
        assert r.status_code == 401

    def test_streamable_http_with_auth_reaches_transport(self):
        with TestClient(make_app(debug=True), follow_redirects=False) as local_client:
            r = local_client.post("/mcp", headers=headers)
        assert r.status_code == 400
        assert r.text == "Invalid Content-Type header"

    def test_sse_no_auth(self):
        r = client.get("/mcp/sse")
        assert r.status_code == 401

    def test_sse_wrong_auth(self):
        r = client.get("/mcp/sse", headers={"authorization": "Bearer wrong-token"})
        assert r.status_code == 401

    def test_messages_no_auth(self):
        r = client.post("/mcp/messages/")
        assert r.status_code == 401


@pytest.mark.usefixtures("_ensure_data")
class TestMcpTools:
    """Test MCP tool functions directly (bypassing SSE transport)."""

    def test_list(self):
        result = mcp_server.list()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == bangumi_1
        assert result[0]["episode"] == 2
        assert result[0]["status_desc"] == "STATUS_FOLLOWED"

    def test_get_filter(self):
        result = mcp_server.get_filter(name=bangumi_1)
        assert result["status"] == "success"
        assert result["data"]["name"] == bangumi_1

    def test_set_filter(self):
        result = mcp_server.set_filter(name=bangumi_1, include="1080p")
        assert result["status"] == "success"
        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert "1080p" in f.include

    def test_seen(self):
        result = mcp_server.seen(name=bangumi_1)
        assert result["status"] == "success"
        assert result["bangumi"] == bangumi_1
        assert result["total_episode"] == 2
        assert result["seen"] == [1, 2]

    def test_seen_forget(self):
        result = mcp_server.seen_forget(name=bangumi_1, episode=2)
        assert result["status"] == "success"
        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert 2 not in f.episodes
        assert 1 in f.episodes

    def test_seen_forget_not_found(self):
        result = mcp_server.seen_forget(name=bangumi_1, episode=999)
        assert result["status"] == "error"

    def test_seen_forget_bangumi_not_followed(self):
        result = mcp_server.seen_forget(name="不存在的番", episode=1)
        assert result["status"] == "error"

    def test_seen_mark(self):
        result = mcp_server.seen_mark(name=bangumi_1, episode=3)
        assert result["status"] == "success"
        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert 1 in f.episodes
        assert 2 in f.episodes
        assert 3 in f.episodes

    def test_seen_mark_bangumi_not_followed(self):
        result = mcp_server.seen_mark(name="不存在的番", episode=1)
        assert result["status"] == "error"

    def test_get_config(self):
        result = mcp_server.get_config()
        assert "data_source" in result
        assert "save_path" in result

    def test_cal(self):
        result = mcp_server.cal()
        assert isinstance(result, dict)
