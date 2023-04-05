import unittest

from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.controllers import add, cal, delete, mark, recreate_source_relatively_table, search


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name_1 = "名侦探柯南"
        self.bangumi_name_2 = "海贼王"

    def test_a_cal(self):
        r = cal()
        assert isinstance(r, dict)
        for day in r.keys():
            assert day.lower() in (x.lower() for x in BANGUMI_UPDATE_TIME)
            assert isinstance(r[day], list)
            for bangumi in r[day]:
                assert "status" in bangumi
                assert "subtitle_group" in bangumi
                assert "name" in bangumi
                assert "update_time" in bangumi
                assert "cover" in bangumi
                assert "episode" in bangumi

    def test_b_add(self):
        r = add(self.bangumi_name_1, 0)
        assert r["status"] == "success", r["message"]
        r = add(self.bangumi_name_1, 0)
        assert r["status"] == "warning", r["message"]
        r = delete(self.bangumi_name_1)
        assert r["status"] == "warning", r["message"]

    def test_c_mark(self):
        add(self.bangumi_name_1, 0)

        r = mark(self.bangumi_name_1, 1)
        assert r["status"] == "success", r["message"]
        r = mark(self.bangumi_name_2, 0)
        assert r["status"] == "error", r["message"]

    def test_d_delete(self):
        r = delete()
        assert r["status"] == "warning", r["message"]
        r = delete(self.bangumi_name_1)
        assert r["status"] == "warning", r["message"]
        r = delete(self.bangumi_name_1)
        assert r["status"] == "warning", r["message"]
        r = delete(self.bangumi_name_2)
        assert r["status"] == "error", r["message"]
        r = delete(clear_all=True, batch=True)
        assert r["status"] == "warning", r["message"]

    def test_e_search(self):
        search(self.bangumi_name_1, dupe=False)

    @staticmethod
    def setUpClass(*args):
        recreate_source_relatively_table()
