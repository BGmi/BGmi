"""Tests for the MCP server tools and auth middleware."""

import pytest
from starlette.testclient import TestClient

from bgmi.config import cfg
from bgmi.front import mcp_server
from bgmi.front.server import make_app
from bgmi.lib.table import Download, Followed, Session

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
        assert result[0]["status"] == "STATUS_FOLLOWED"
        assert "status_code" not in result[0]
        assert "updated_time" not in result[0]
        assert result[0]["updated_at"] is None

    def test_set_status_accepts_semantic_status(self):
        result = mcp_server.set_status(name=bangumi_1, status="STATUS_UPDATED_TODAY")
        assert result["status"] == "success"
        assert result["follow_status"] == "STATUS_UPDATED_TODAY"

        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert f.status == Followed.STATUS_UPDATED
        assert f.updated_time > 0

    def test_set_status_rejects_unknown_status(self):
        result = mcp_server.set_status(name=bangumi_1, status="watching")
        assert result["status"] == "error"

    def test_set_status_does_not_manage_delete_or_end_status(self):
        result = mcp_server.set_status(name=bangumi_1, status="STATUS_DELETED")
        assert result["status"] == "error"

        result = mcp_server.set_status(name=bangumi_1, status="STATUS_END")
        assert result["status"] == "error"

    def test_get_filter(self):
        result = mcp_server.get_filter(name=bangumi_1)
        assert result["status"] == "success"
        assert result["data"]["name"] == bangumi_1

    def test_set_filter(self):
        result = mcp_server.set_filter(name=bangumi_1, include=["1080p"])
        assert result["status"] == "success"
        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert "1080p" in f.include

    def test_set_filter_can_clear_lists(self):
        mcp_server.set_filter(name=bangumi_1, include=["1080p"])
        result = mcp_server.set_filter(name=bangumi_1, include=[])
        assert result["status"] == "success"
        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert f.include == []

    def test_download_status_returns_newest_limited_tasks(self):
        with Session.begin() as tx:
            tx.query(Download).delete()
            tx.add(
                Download(
                    bangumi_name="Old",
                    title="old",
                    episode=1,
                    download="magnet:?xt=old",
                    status=Download.STATUS_DOWNLOADING,
                )
            )
            tx.add(
                Download(
                    bangumi_name="Middle",
                    title="middle",
                    episode=2,
                    download="magnet:?xt=middle",
                    status=Download.STATUS_DOWNLOADING,
                )
            )
            tx.add(
                Download(
                    bangumi_name="New",
                    title="new",
                    episode=3,
                    download="magnet:?xt=new",
                    status=Download.STATUS_DOWNLOADING,
                )
            )

        result = mcp_server.download_status(limit=2)

        assert [item["name"] for item in result] == ["New", "Middle"]

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

    def test_seen_mark_batch(self):
        result = mcp_server.seen_mark(name=bangumi_1, episodes=[3, 4])
        assert result["status"] == "success"
        assert result["episodes"] == [3, 4]
        f = Followed.get(Followed.bangumi_name == bangumi_1)
        assert f.episodes == {1, 2, 3, 4}

    def test_seen_mark_bangumi_not_followed(self):
        result = mcp_server.seen_mark(name="不存在的番", episode=1)
        assert result["status"] == "error"

    def test_cal(self):
        result = mcp_server.cal()
        assert isinstance(result, dict)
