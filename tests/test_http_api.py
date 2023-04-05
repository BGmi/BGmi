import json
import logging
import os
import random
import string
from unittest import mock

from tornado.testing import AsyncHTTPTestCase

from bgmi.config import cfg
from bgmi.front.base import COVER_URL
from bgmi.front.index import get_player
from bgmi.front.server import make_app

logging.basicConfig(level=logging.DEBUG)


def random_word(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class ApiTestCase(AsyncHTTPTestCase):
    headers = {"BGmi-Token": cfg.http.admin_token, "Content-Type": "application/json"}
    bangumi_1 = "名侦探柯南"
    bangumi_2 = "海贼王"
    bangumi_3 = "黑色五叶草"

    def get_app(self):
        self.app = make_app()
        return self.app

    def test_a_auth(self):
        r = self.fetch("/api/auth", method="POST", body=json.dumps({"token": cfg.http.admin_token}))
        assert r.code == 200
        res = self.parse_response(r)
        assert res["status"] == "success"

        r = self.fetch("/api/auth", method="POST", body=json.dumps({"token": "3"}))
        assert r.code == 400
        res = self.parse_response(r)
        assert res["status"] == "error"

    def test_a_cal(self):
        m = mock.Mock(return_value={"status": "warning", "data": {"hello": "world"}})
        with mock.patch("bgmi.front.admin.API_MAP_GET", {"cal": m}):
            r = self.fetch("/api/cal", method="GET")
            res = self.parse_response(r)
            assert res["data"] == {"hello": "world"}
            m.assert_called_once_with()

    def test_b_add(self):
        m = mock.Mock(return_value={"status": "warning"})
        with mock.patch("bgmi.front.admin.API_MAP_POST", {"add": m}):
            r = self.fetch(
                "/api/add",
                method="POST",
                headers=self.headers,
                body=json.dumps({"name": self.bangumi_1}),
            )
            assert r.code == 200
            m.assert_called_once_with(name=self.bangumi_1)

    def test_c_delete(self):
        m = mock.Mock(return_value={"status": "warning"})
        with mock.patch("bgmi.front.admin.API_MAP_POST", {"delete": m}):
            m.return_value = {"status": "warning"}
            r = self.fetch(
                "/api/delete",
                method="POST",
                headers=self.headers,
                body=json.dumps({"name": self.bangumi_2}),
            )
            assert r.code == 200
            r = self.parse_response(r)
            assert r["status"] == "warning"
            m.assert_called_once_with(name=self.bangumi_2)

    def test_e_mark(self):
        m = mock.Mock(return_value={"status": "success"})
        episode = random.randint(0, 10)
        with mock.patch("bgmi.front.admin.API_MAP_POST", {"mark": m}):
            r = self.fetch(
                "/api/mark",
                method="POST",
                headers=self.headers,
                body=json.dumps({"name": self.bangumi_1, "episode": episode}),
            )
            m.assert_called_once_with(**{"name": self.bangumi_1, "episode": episode})

            assert r.code == 200

    def test_d_filter(self):
        include = random_word(5)
        exclude = random_word(5)
        regex = random_word(5)

        m = mock.Mock(return_value={"status": "success", "data": {"h": "w"}})
        with mock.patch("bgmi.front.admin.API_MAP_POST", {"filter": m}):
            r = self.fetch(
                "/api/filter",
                method="POST",
                body=json.dumps({"name": self.bangumi_1}),
                headers=self.headers,
            )

            assert r.code == 200
            res = self.parse_response(r)
            assert res["data"] == {"h": "w"}
            assert res["status"] == "success"
            m.assert_called_once_with(name=self.bangumi_1)

            data = {
                "name": self.bangumi_1,
                "include": include,
                "regex": regex,
                "exclude": exclude,
                "subtitle": "a,b,c",
            }
            self.fetch(
                "/api/filter",
                method="POST",
                body=json.dumps(data),
                headers=self.headers,
            )
            m.assert_called_with(**data)

    def test_e_index(self):
        m = mock.Mock(return_value={"status": "success", "data": {"h": "w"}})
        m2 = mock.Mock(
            return_value=[
                {"bangumi_name": "233", "updated_time": 3, "cover": "233"},
                {"bangumi_name": "2333", "updated_time": 20000000000, "cover": "2333"},
            ]
        )
        with mock.patch("bgmi.front.index.get_player", m), mock.patch("bgmi.lib.table.Followed.get_all_followed", m2):
            response = self.fetch("/api/index", method="GET")
        assert response.code == 200
        r = self.parse_response(response)
        assert COVER_URL + "/2333" == r["data"][0]["cover"], json.dumps(r["data"])
        m.assert_has_calls(
            [
                mock.call("233"),
                mock.call("2333"),
                mock.call("TEST_BANGUMI"),
            ],
            any_order=True,
        )
        assert m.call_count == 3

    def test_resource_ics(self):
        r = self.fetch("/resource/feed.xml")
        assert r.code == 200

    def test_resource_feed(self):
        r = self.fetch("/resource/calendar.ics")
        assert r.code == 200

    def test_no_auth(self):
        r = self.fetch("/api/add", method="POST", body=json.dumps({"name": self.bangumi_1}))
        assert r.code == 401

    @staticmethod
    def parse_response(response):
        r = json.loads(response.body.decode("utf-8"))
        return r


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
