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
from bgmi.lib.table import Followed

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


def test_a_cal(ensure_data):
    r = client.get("/api/admin/calendar", headers=headers)
    assert r.status_code == 200, r.text


def test_b_add(ensure_data):
    r = client.post(
        "/api/admin/add",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 200, r.text


def test_c_delete(ensure_data):
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


def test_e_mark(ensure_data):
    episode = random.randint(0, 10)
    r = client.post(
        "/api/mark",
        headers=headers,
        json={"bangumi": bangumi_1, "episode": episode},
    )

    assert r.status_code == 200
    assert Followed.get(Followed.bangumi_name == bangumi_1).episode == episode


def test_d_filter(ensure_data):
    include = random_word(5)
    exclude = random_word(5)
    regex = random_word(5)

    r = client.get(f"/api/admin/filter/{bangumi_1}", headers=headers)
    assert r.status_code == 200

    res = r.json()

    assert res["data"] == {"h": "w"}
    assert res["status"] == "success"

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


def test_e_index(ensure_data):
    response = client.get("/api/index")
    assert response.status_code == 200, response.text
    r = response.json()
    assert COVER_URL + "/2333" == r["data"][0]["cover"], r["data"]


def test_resource_feed(ensure_data):
    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200


def test_no_auth(ensure_data):
    r = client.post("/api/admin/add", json={"bangumi": bangumi_1})
    assert r.status_code == 401, r.text


def parse_response(response: Response):
    return response.json()


def test_get_player(ensure_data):
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
