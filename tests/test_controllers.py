import unittest

from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.controllers import (
    add,
    cal,
    delete,
    mark,
    recreate_source_relatively_table,
    search,
)
from bgmi.main import setup


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name_1 = "名侦探柯南"
        self.bangumi_name_2 = "海贼王"

    def test_a_cal(self):
        r = cal()
        self.assertIsInstance(r, dict)
        for day in r.keys():
            self.assertIn(day.lower(), [x.lower() for x in BANGUMI_UPDATE_TIME])
            self.assertIsInstance(r[day], list)
            for bangumi in r[day]:
                self.assertIn("status", bangumi)
                self.assertIn("subtitle_group", bangumi)
                self.assertIn("name", bangumi)
                self.assertIn("update_time", bangumi)
                self.assertIn("cover", bangumi)

    def test_b_add(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r["status"], "success", r["message"])
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r["status"], "warning", r["message"])
        r = delete(self.bangumi_name_1)
        self.assertEqual(r["status"], "warning", r["message"])

    def test_c_mark(self):
        add(self.bangumi_name_1, 0)

        r = mark(self.bangumi_name_1, 1)
        self.assertEqual(r["status"], "success", r["message"])
        r = mark(self.bangumi_name_1, None)
        self.assertEqual(r["status"], "info", r["message"])
        r = mark(self.bangumi_name_2, 0)
        self.assertEqual(r["status"], "error", r["message"])

    def test_d_delete(self):
        r = delete()
        self.assertEqual(r["status"], "warning", r["message"])
        r = delete(self.bangumi_name_1)
        self.assertEqual(r["status"], "warning", r["message"])
        r = delete(self.bangumi_name_1)
        self.assertEqual(r["status"], "warning", r["message"])
        r = delete(self.bangumi_name_2)
        self.assertEqual(r["status"], "error", r["message"])
        r = delete(clear_all=True, batch=True)
        self.assertEqual(r["status"], "warning", r["message"])

    def test_e_search(self):
        r = search(self.bangumi_name_1, dupe=False)

    @staticmethod
    def setUpClass():
        setup()
        recreate_source_relatively_table()
