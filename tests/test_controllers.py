# -*- coding: utf-8 -*-

import unittest
from unittest import mock

import bgmi.lib.controllers
from bgmi.lib.models import Bangumi, Followed
from bgmi.website.base import BaseWebsite

w = lambda: mock.Mock(spec=BaseWebsite)

from tests.mock_websites import MockDateSource


@mock.patch('bgmi.website.DATA_SOURCE_MAP', MockDateSource)
class ControllersTest(unittest.TestCase):
    """
    at the beginning of each test,
    bangumi 1 is followed
    bangumi 2 is not followed
    """
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'

    def setUp(self):
        Followed.delete().execute()
        Followed.create(bangumi_name=self.bangumi_name_1,
                        status=bgmi.lib.controllers.Followed.STATUS.FOLLOWED)

    def test_cal(self):
        r = bgmi.lib.controllers.cal()
        self.assertIsInstance(r, dict)
        for day in r.keys():
            self.assertIn(day.lower(), [x.lower() for x in Bangumi.week])
            self.assertIsInstance(r[day], list)
            for bangumi in r[day]:
                # {'bangumi_name': 'TEST_BANGUMI', 'cover': '', 'update_time': 'Mon', 'name': 'TEST_BANGUMI', 'status': 1,
                #  'updated_time': 0, 'subtitle_group': '', 'episode': 0}
                for key in ['name', 'cover', 'update_time', 'status', 'episode']:
                    self.assertIn(key, bangumi)

    def test_add(self):
        r = bgmi.lib.controllers.add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'warning')
        f = Followed.get(bangumi_name=self.bangumi_name_1)  # type: Followed
        self.assertEqual(f.status, Followed.STATUS.FOLLOWED)

        r = bgmi.lib.controllers.add(self.bangumi_name_2, episode=4)
        self.assertEqual(r['status'], 'success')
        f = Followed.get(bangumi_name=self.bangumi_name_2)  # type: Followed
        self.assertEqual(f.status, Followed.STATUS.FOLLOWED)
        self.assertEqual(f.episode, 4)

    def test_mark(self):
        r = bgmi.lib.controllers.mark(self.bangumi_name_1, 1)
        self.assertEqual(r['status'], 'success')
        r = bgmi.lib.controllers.mark(self.bangumi_name_1, None)
        self.assertEqual(r['status'], 'info')
        r = bgmi.lib.controllers.mark(self.bangumi_name_2, 0)
        self.assertEqual(r['status'], 'error')

    def test_delete(self):
        r = bgmi.lib.controllers.delete()
        self.assertEqual(r['status'], 'warning')
        r = bgmi.lib.controllers.delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')
        r = bgmi.lib.controllers.delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')
        r = bgmi.lib.controllers.delete(self.bangumi_name_2)
        self.assertEqual(r['status'], 'error')
        r = bgmi.lib.controllers.delete(clear_all=True, batch=True)
        self.assertEqual(r['status'], 'warning')

    def test_search(self):
        r = bgmi.lib.controllers.search(self.bangumi_name_1, dupe=False)
