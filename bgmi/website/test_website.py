import unittest

import bgmi.website.bangumi_moe
import bgmi.website.mikan
import bgmi.website.share_dmhy
from bgmi.website import BaseWebsite


class BasicT:
    bangumi_name_1 = 'BANGUMI_1'
    bangumi_name_2 = 'BANGUMI_2'

    w: BaseWebsite

    def test_info(self):
        bs, gs = self.w.fetch_bangumi_calendar_and_subtitle_group()
        b = {}
        for bangumi in bs:
            assert 'status' in bangumi
            assert 'subtitle_group' in bangumi
            assert 'name' in bangumi
            assert 'keyword' in bangumi
            assert 'update_time' in bangumi
            assert 'cover' in bangumi
            if bangumi['name'] == self.bangumi_name_1:
                b = bangumi

        for subtitle_group in gs:
            assert 'id' in subtitle_group
            assert 'name' in subtitle_group

        assert b

        es = self.w.fetch_episode_of_bangumi(b['keyword'], 3)
        for episode in es:
            assert 'download' in episode
            assert 'subtitle_group' in episode
            assert 'title' in episode
            assert 'episode' in episode
            assert 'time' in episode

    def test_search(self):
        r = self.w.search_by_keyword(self.bangumi_name_1, count=3)
        for b in r:
            assert 'name' in b
            assert 'download' in b
            assert 'title' in b
            assert 'episode' in b


class MikanProjectTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'
    w = bgmi.website.mikan.Mikanani()


class DmhyTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名偵探柯南'
    bangumi_name_2 = '海賊王'
    w = bgmi.website.share_dmhy.DmhySource()


class BangumiMoeTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'
    w = bgmi.website.bangumi_moe.BangumiMoe()
