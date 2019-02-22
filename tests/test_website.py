# -*- coding: utf-8 -*-

import unittest

import bgmi.website
import bgmi.utils.utils

# from bgmi.lib.fetch import website
# from bgmi.website.base import BaseWebsite


class BasicT:
    bangumi_name_1 = 'BANGUMI_1'
    bangumi_name_2 = 'BANGUMI_2'

    # w  # type: BaseWebsite

    def test_info(self):
        bs, gs = self.w.fetch_bangumi_calendar_and_subtitle_group()
        b = {}
        for bangumi in bs:
            self.assertIn("status", bangumi)
            self.assertIn("subtitle_group", bangumi)
            self.assertIn("name", bangumi)
            self.assertIn("keyword", bangumi)
            self.assertIn("update_time", bangumi)
            self.assertIn("cover", bangumi)
            if bangumi['name'] == self.bangumi_name_1:
                b = bangumi

        for subtitle_group in gs:
            self.assertIn('id', subtitle_group)
            self.assertIn('name', subtitle_group)
        self.assertTrue(bool(b))
        es = self.w.fetch_episode_of_bangumi(b['keyword'])
        for episode in es:
            self.assertIn('download', episode)
            self.assertIn('subtitle_group', episode)
            self.assertIn('title', episode)
            self.assertIn('episode', episode)
            self.assertIn('time', episode)

    def test_search(self):
        r = self.w.search_by_keyword(self.bangumi_name_1, count=3)
        for b in r:
            self.assertIn('name', b)
            self.assertIn('download', b)
            self.assertIn('title', b)
            self.assertIn('episode', b)

    # @staticmethod
    # def setUpClass():
    #     setup()
    #     recreate_source_relatively_table()


class MikanProjectTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'
    w = bgmi.website.Mikanani()


class DmhyTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名偵探柯南'
    bangumi_name_2 = '海賊王'
    w = bgmi.website.DmhySource()


class BangumiMoeTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'
    w = bgmi.website.BangumiMoe()
