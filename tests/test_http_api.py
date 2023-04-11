import os
import random
import string
from urllib.parse import quote

import pytest
from requests import Response
from starlette.testclient import TestClient

from bgmi.config import cfg
from bgmi.front.index import get_player
from bgmi.front.routes import COVER_URL
from bgmi.front.server import make_app
from bgmi.lib.table import Followed


def random_word(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


client = TestClient(make_app())

headers = {"authorization": f"Bearer {cfg.http.admin_token}"}

bangumi_1 = "名侦探柯南"
bangumi_2 = "海贼王"


def test_no_auth(ensure_data):
    r = client.post("/api/admin/auth")
    assert r.status_code == 403, r.text


def test_calendar(ensure_data):
    r = client.get("/api/calendar")
    assert r.status_code == 200, r.text


def test_b_add(ensure_data):
    r = client.post(
        "/api/admin/add",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 200, r.text


def test_delete(ensure_data):
    r = client.post(
        "/api/admin/delete",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 200, r.text
    assert Followed.get(Followed.bangumi_name == bangumi_1).status == Followed.STATUS_DELETED


def test_delete_not_found(ensure_data):
    r = client.post(
        "/api/admin/delete",
        headers=headers,
        json={"bangumi": bangumi_2},
    )
    assert r.status_code == 404, r.text


@pytest.mark.skip("need re-design")
def test_e_mark(ensure_data):
    episode = random.randint(0, 10)
    r = client.post(
        "/api/admin/mark",
        headers=headers,
        json={"bangumi": bangumi_1, "episode": episode},
    )

    assert r.status_code == 200
    assert Followed.get(Followed.bangumi_name == bangumi_1).episode == episode


def test_filter(ensure_data):
    r = client.get(f"/api/admin/filter/{quote(bangumi_1)}", headers=headers)
    assert r.status_code == 200, r.text

    r = client.patch(
        f"/api/admin/filter/{quote(bangumi_1)}",
        json={"include": ["1", "2", "3"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    assert Followed.get(Followed.bangumi_name == bangumi_1).include == ["1", "2", "3"]


def test_index(ensure_data):
    response = client.get("/api/index/index")
    assert response.status_code == 200, response.text
    r = response.json()
    assert r["data"], r
    assert r["data"][0].get("cover"), r
    assert COVER_URL + "/hello" == r["data"][0]["cover"], r


def test_resource_feed(ensure_data):
    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200


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
