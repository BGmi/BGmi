import logging
import os
import random
import string
from unittest import mock

from requests import Response
from starlette.testclient import TestClient

from bgmi.config import cfg
from bgmi.front.index import get_player
from bgmi.front.routes import COVER_URL
from bgmi.front.server import make_app

logging.basicConfig(level=logging.DEBUG)


def random_word(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


logger = logging.getLogger()
logger.setLevel(logging.ERROR)

client = TestClient(make_app())

headers = {"authorization": f"Bearer {cfg.http.admin_token}"}
bangumi_1 = "名侦探柯南"
bangumi_2 = "海贼王"
bangumi_3 = "黑色五叶草"


def test_a_cal():
    r = client.get("/api/admin/calendar", headers=headers)
    assert r.status_code == 200


def test_b_add():
    r = client.post(
        "/api/add",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 200


def test_c_delete():
    m = mock.Mock(return_value={"status": "warning"})
    with mock.patch("bgmi.front.admin.API_MAP_POST", {"delete": m}):
        m.return_value = {"status": "warning"}
        r = client.post(
            "/api/delete",
            headers=headers,
            json={"name": bangumi_2},
        )
        assert r.status_code == 200
        r = parse_response(r)
        assert r["status"] == "warning"
        m.assert_called_once_with(name=bangumi_2)


def test_e_mark():
    m = mock.Mock(return_value={"status": "success"})
    episode = random.randint(0, 10)
    with mock.patch("bgmi.front.admin.API_MAP_POST", {"mark": m}):
        r = client.post(
            "/api/mark",
            headers=headers,
            json={"name": bangumi_1, "episode": episode},
        )
        m.assert_called_once_with(**{"name": bangumi_1, "episode": episode})

        assert r.status_code == 200


def test_d_filter():
    include = random_word(5)
    exclude = random_word(5)
    regex = random_word(5)

    m = mock.Mock(return_value={"status": "success", "data": {"h": "w"}})
    with mock.patch("bgmi.front.admin.API_MAP_POST", {"filter": m}):
        r = client.post(
            "/api/filter",
            json={"name": bangumi_1},
            headers=headers,
        )

        assert r.status_code == 200
        res = r.json()
        assert res["data"] == {"h": "w"}
        assert res["status"] == "success"
        m.assert_called_once_with(name=bangumi_1)

        data = {
            "name": bangumi_1,
            "include": include,
            "regex": regex,
            "exclude": exclude,
            "subtitle": "a,b,c",
        }
        client.post(
            "/api/filter",
            json=data,
            headers=headers,
        )
        m.assert_called_with(**data)


def test_e_index():
    m = mock.Mock(return_value={"status": "success", "data": {"h": "w"}})
    m2 = mock.Mock(
        return_value=[
            {"bangumi_name": "233", "updated_time": 3, "cover": "233"},
            {"bangumi_name": "2333", "updated_time": 20000000000, "cover": "2333"},
        ]
    )
    with mock.patch("bgmi.front.index.get_player", m), mock.patch("bgmi.lib.table.Followed.get_all_followed", m2):
        response = client.get("/api/index")
    assert response.status_code == 200
    r = response.json()
    assert COVER_URL + "/2333" == r["data"][0]["cover"], r["data"]
    m.assert_has_calls(
        [
            mock.call("233"),
            mock.call("2333"),
            mock.call("TEST_BANGUMI"),
        ],
        any_order=True,
    )
    assert m.call_count == 3


def test_resource_feed():
    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200


def test_no_auth():
    r = client.post("/api/admin/add", json={"bangumi": bangumi_1})
    assert r.status_code == 401


def parse_response(response: Response):
    return response.json()


def test_get_player():
    bangumi_name = "test"
    save_dir = os.path.join(cfg.save_path)
    episode1_dir = os.path.join(save_dir, bangumi_name, "1", "episode1")
    if not os.path.exists(episode1_dir):
        os.makedirs(episode1_dir)
    open(os.path.join(episode1_dir, "1.mp4"), "a").close()

    episode2_dir = os.path.join(save_dir, bangumi_name, "2")
    if not os.path.exists(episode2_dir):
        os.makedirs(episode2_dir)
    open(os.path.join(episode2_dir, "2.mkv"), "a").close()

    bangumi_dict = {"player": get_player(bangumi_name)}

    assert 1 in bangumi_dict["player"]
    assert bangumi_dict["player"][1]["path"] == f"/{bangumi_name}/1/episode1/1.mp4"

    assert 2 in bangumi_dict["player"]
    assert bangumi_dict["player"][2]["path"] == f"/{bangumi_name}/2/2.mkv"
