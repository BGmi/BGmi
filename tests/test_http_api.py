import os
import random
import shutil
import string
from unittest import mock
from urllib.parse import quote

import pytest
from requests import Response
from starlette.testclient import TestClient

from bgmi.config import cfg
from bgmi.front.index import get_player
from bgmi.front.routes import COVER_URL
from bgmi.front.server import make_app
from bgmi.lib.table import Followed, Scripts, Session


def random_word(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


client = TestClient(make_app(debug=True))

headers = {"authorization": f"Bearer {cfg.http.admin_token}"}

bangumi_1 = "名侦探柯南"
bangumi_2 = "海贼王"


@pytest.mark.usefixtures("_ensure_data")
def test_no_auth():
    r = client.post("/api/admin/auth")
    assert r.status_code == 403, r.text


@pytest.mark.usefixtures("_ensure_data")
def test_calendar():
    r = client.get("/api/calendar")
    assert r.status_code == 200, r.text


@pytest.mark.usefixtures("_ensure_data")
def test_b_add():
    r = client.post(
        "/api/admin/add",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 200, r.text


@pytest.mark.usefixtures("_ensure_data")
def test_b_add_new():
    r = client.post(
        "/api/admin/add",
        headers=headers,
        json={"bangumi": bangumi_2, "season": 2, "episode_offset": -12},
    )
    assert r.status_code == 200, r.text
    f = Followed.get(Followed.bangumi_name == bangumi_2)
    assert f.status == Followed.STATUS_FOLLOWED
    assert f.episodes == set()
    assert f.season == 2
    assert f.episode_offset == -12


@pytest.mark.usefixtures("_ensure_data")
def test_b_add_not_found():
    r = client.post(
        "/api/admin/add",
        headers=headers,
        json={"bangumi": "不存在的番"},
    )
    assert r.status_code == 404


@pytest.mark.usefixtures("_ensure_data")
def test_delete():
    r = client.post(
        "/api/admin/delete",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 200, r.text
    assert Followed.get(Followed.bangumi_name == bangumi_1).status == Followed.STATUS_DELETED


@pytest.mark.usefixtures("_ensure_data")
def test_delete_not_found():
    r = client.post(
        "/api/admin/delete",
        headers=headers,
        json={"bangumi": bangumi_2},
    )
    assert r.status_code == 404, r.text


@pytest.mark.usefixtures("_ensure_data")
def test_seen():
    r = client.get(f"/api/admin/seen/{quote(bangumi_1)}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json() == {
        "bangumi": bangumi_1,
        "total_episode": 2,
        "seen": [1, 2],
    }


@pytest.mark.usefixtures("_ensure_data")
def test_seen_forget():
    r = client.post(
        "/api/admin/seen_forget",
        headers=headers,
        json={"bangumi": bangumi_1, "episode": 2},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {
        "bangumi": bangumi_1,
        "episode": 2,
        "seen": [1],
    }
    f = Followed.get(Followed.bangumi_name == bangumi_1)
    assert 2 not in f.episodes
    assert 1 in f.episodes


@pytest.mark.usefixtures("_ensure_data")
def test_seen_forget_not_found():
    r = client.post(
        "/api/admin/seen_forget",
        headers=headers,
        json={"bangumi": bangumi_1, "episode": 999},
    )
    assert r.status_code == 404


@pytest.mark.usefixtures("_ensure_data")
def test_seen_forget_batch():
    r = client.post(
        "/api/admin/seen_forget",
        headers=headers,
        json={"bangumi": bangumi_1, "episodes": [1, 2]},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {
        "bangumi": bangumi_1,
        "episodes": [1, 2],
        "seen": [],
    }


@pytest.mark.usefixtures("_ensure_data")
def test_seen_mark():
    r = client.post(
        "/api/admin/seen_mark",
        headers=headers,
        json={"bangumi": bangumi_1, "episode": 3},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {
        "bangumi": bangumi_1,
        "episode": 3,
        "seen": [1, 2, 3],
    }
    f = Followed.get(Followed.bangumi_name == bangumi_1)
    assert 1 in f.episodes
    assert 2 in f.episodes
    assert 3 in f.episodes


@pytest.mark.usefixtures("_ensure_data")
def test_seen_mark_batch():
    r = client.post(
        "/api/admin/seen_mark",
        headers=headers,
        json={"bangumi": bangumi_1, "episodes": [3, 4]},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {
        "bangumi": bangumi_1,
        "episodes": [3, 4],
        "seen": [1, 2, 3, 4],
    }


@pytest.mark.usefixtures("_ensure_data")
def test_seen_mark_requires_episode():
    r = client.post(
        "/api/admin/seen_mark",
        headers=headers,
        json={"bangumi": bangumi_1},
    )
    assert r.status_code == 404


@pytest.mark.usefixtures("_ensure_data")
def test_filter():
    r = client.get(f"/api/admin/filter/{quote(bangumi_1)}", headers=headers)
    assert r.status_code == 200, r.text

    r = client.patch(
        f"/api/admin/filter/{quote(bangumi_1)}",
        json={"include": ["1", "2", "3"]},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    assert Followed.get(Followed.bangumi_name == bangumi_1).include == ["1", "2", "3"]


@pytest.mark.usefixtures("_ensure_data")
def test_index():
    with mock.patch("bgmi.front.routes.get_player") as get_player_mock:
        response = client.get("/api/index/index")
    get_player_mock.assert_not_called()

    assert response.status_code == 200, response.text
    r = response.json()
    assert r["data"], r
    assert r["data"][0].get("cover"), r
    assert r["data"][0]["id"] == "1", r
    assert COVER_URL + "/hello" == r["data"][0]["cover"], r
    assert all("episodes" not in item for item in r["data"])
    assert all("player" not in item for item in r["data"])


@pytest.mark.usefixtures("_ensure_data")
def test_player_by_id():
    episode_dir = cfg.save_path / bangumi_1 / "1"
    episode_dir.mkdir(parents=True, exist_ok=True)
    (episode_dir / "1.mp4").write_text("")

    response = client.get("/api/player/1")
    assert response.status_code == 200, response.text
    r = response.json()
    assert r["data"]["id"] == "1"
    assert r["data"]["bangumi_name"] == bangumi_1
    assert r["data"]["player"]["1"]["path"] == f"/{bangumi_1}/1/1.mp4"


@pytest.mark.usefixtures("_ensure_data")
def test_script_player_by_id():
    name = "script bangumi"
    episode_dir = cfg.save_path / name / "1"
    episode_dir.mkdir(parents=True, exist_ok=True)
    (episode_dir / "1.mp4").write_text("")
    with Session.begin() as tx:
        tx.add(Scripts(bangumi_name=name, episodes={1}, status=Followed.STATUS_FOLLOWED))

    items = client.get("/api/index/index").json()["data"]
    bangumi_id = next(item["id"] for item in items if item["bangumi_name"] == name)
    response = client.get(f"/api/player/{bangumi_id}")

    assert response.status_code == 200, response.text
    assert response.json()["data"]["player"]["1"]["path"] == f"/{name}/1/1.mp4"


@pytest.mark.usefixtures("_ensure_data")
def test_player_not_found():
    assert client.get("/api/player/not-found").status_code == 404


@pytest.mark.usefixtures("_ensure_data")
def test_resource_feed():
    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200


def parse_response(response: Response):
    return response.json()


@pytest.mark.usefixtures("_ensure_data")
def test_get_player():
    bangumi_name = "test"
    save_dir = os.path.join(cfg.save_path)
    episode1_dir = os.path.join(save_dir, bangumi_name, "1", "episode1")
    if not os.path.exists(episode1_dir):
        os.makedirs(episode1_dir)
    with open(os.path.join(episode1_dir, "1.mp4"), "a"):
        pass

    episode2_dir = os.path.join(save_dir, bangumi_name, "2")
    if not os.path.exists(episode2_dir):
        os.makedirs(episode2_dir)
    with open(os.path.join(episode2_dir, "2.mkv"), "a"):
        pass

    bangumi_dict = {"player": get_player(bangumi_name, episodes={1, 2, 3})}

    assert 1 in bangumi_dict["player"]
    assert bangumi_dict["player"][1]["path"] == f"/{bangumi_name}/1/episode1/1.mp4"

    assert 2 in bangumi_dict["player"]
    assert bangumi_dict["player"][2]["path"] == f"/{bangumi_name}/2/2.mkv"


def test_get_player_with_path_formatter():
    bangumi_name = "相反的你和我 第二季"
    target_dir = cfg.save_path / "相反的你和我" / "S02"
    old_enable = cfg.enable_path_formatter
    old_formatter = cfg.path_formatter

    try:
        cfg.enable_path_formatter = True
        cfg.path_formatter = "{name}/S{season:02d}/S{season:02d}E{episode:02d}.{suffix}"
        shutil.rmtree(cfg.save_path / "相反的你和我", ignore_errors=True)
        target_dir.mkdir(parents=True)
        (target_dir / "S02E02.txt").write_text("not video")
        (target_dir / "S02E01.mkv").write_text("video")
        assert get_player(bangumi_name, episodes={13}, season=2, episode_offset=-12) == {
            13: {"path": "/相反的你和我/S02/S02E01.mkv"}
        }
        assert get_player(bangumi_name, episodes={14}, season=2, episode_offset=-12) == {}
    finally:
        cfg.enable_path_formatter = old_enable
        cfg.path_formatter = old_formatter
        shutil.rmtree(cfg.save_path / "相反的你和我", ignore_errors=True)
