from unittest import mock, TestCase

from bgmi.lib.models import Bangumi
from bgmi.website import DataSource, DATA_SOURCE_MAP
from bgmi.website.base import BaseWebsite

w = lambda: mock.Mock(spec=BaseWebsite)

from bgmi.website import DATA_SOURCE_MAP

import json


def fetch_data():
    for key, value in DATA_SOURCE_MAP.items():
        with open('./data/website/{}.fetch_bangumi_calendar_and_subtitle_group.json'.format(key),
                  'w+', encoding='utf8') as f:
            json.dump(value.fetch_bangumi_calendar_and_subtitle_group(), f,
                      indent=2, ensure_ascii=False)

        obj = {}
        for bangumi in value.get_bangumi_calendar_and_subtitle_group()[0]:
            obj[bangumi.keyword] = value.fetch_episode_of_bangumi(bangumi.keyword, max_page=1)[:3]
        with open('./data/website/{}.bangumi-episode.json'.format(key),
                  'w+', encoding='utf8') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)


class W(BaseWebsite):
    website_id = ''

    def __init__(self, website_id):
        self.website_id = website_id
        pass

    def fetch_bangumi_calendar_and_subtitle_group(self):
        with open('./tests/data/website/{}.fetch_bangumi_calendar_and_subtitle_group.json'
                      .format(self.website_id),
                  'r', encoding='utf8') as f:
            return json.load(f)

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=1):
        with open('./tests/data/website/{}.bangumi-episode.json'.format(self.website_id),
                  'r', encoding='utf8') as f:
            return json.load(f).get(bangumi_id, [])

    def search_by_keyword(self, keyword, count=None):
        episode_list = []

        with open('./tests/data/website/{}.bangumi-episode.json'.format(self.website_id),
                  'r', encoding='utf8') as f:
            b = json.load(f)

        for li in b.values():
            for episode in li:
                if keyword in episode:
                    episode['name'] = keyword
                    episode_list.append(episode)
        return episode_list


MockDateSource = {key: W(website_id=key) for key in DATA_SOURCE_MAP}


@mock.patch('bgmi.website.DATA_SOURCE_MAP', MockDateSource)
class TestDataSourceUtils(TestCase):
    def test_filter_keyword_correct_regex_include_match(self):
        l = [{
            'title': 'bangumi'
        }]
        e = DataSource.Utils.filter_keyword(l, regex='bangumi')
        self.assertListEqual(e, l)

    def test_filter_keyword_correct_regex_remove_not_match(self):
        l = [{
            'title': 'b'
        }]
        e = DataSource.Utils.filter_keyword(l, regex='bangumi')
        self.assertEqual(len(e), 0)

    def test_filter_keyword_wrong_regex_filter_nothing(self):
        l = [{
            'title': 'bangumi'
        }]
        e = DataSource.Utils.filter_keyword(l, regex='bang[umi')
        self.assertListEqual(e, l)

    def test_remove_duplicated_bangumi(self):
        l = [{
            'title': 'bangumi',
            'episode': 1,
        }, {
            'title': 'bangumi',
            'episode': 1,
        }, {
            'title': 'bangumi',
            'episode': 2,
        }, ]
        e = DataSource.Utils.remove_duplicated_bangumi(l)
        self.assertEqual(len(e), 2)
        self.assertListEqual(e, [l[0], l[-1]])


@mock.patch('bgmi.website.DATA_SOURCE_MAP', MockDateSource)
# class TestDataSource(TestCase):
class TestDataSource():

    def test_bangumi_calendar(self):
        DataSource().fetch()
        raise Exception

    def test_init_data(self):
        raise Exception

    def test_fetch(self, save=False, group_by_weekday=True):
        raise Exception

    def test_save_data(self):
        """
        save bangumi dict to database

        # :type data: dict
        """
        raise Exception

        pass
        # data.save()

    def test_get_maximum_episode(self):
        """

        :type max_page: str
        :param max_page:
        :type bangumi: object
        :type ignore_old_row: bool
        :param ignore_old_row:
        :type bangumi: Bangumi
        :param subtitle:
        :type subtitle: bool
        """
        raise Exception

    def test_fetch_episode(self):
        """
        :type filter_obj: Filter
        :type source: str
        :type bangumi_obj: Bangumi
        :type subtitle_group: str
        :type include: str
        :type exclude: str
        :type regex: str
        :type max_page: int
        """
        raise Exception

    @staticmethod
    def test_followed_bangumi():
        """

        :return: list of bangumi followed
        :rtype: list[dict]
        """
        raise Exception

    def test_search_by_keyword(self):  # pragma: no cover
        """
        return a list of dict with at least 4 key: download, name, title, episode
        example:
        ```
            [
                {
                    'name':"路人女主的养成方法",
                    'download': 'magnet:?xt=urn:btih:what ever',
                    'title': "[澄空学园] 路人女主的养成方法 第12话 MP4 720p  完",
                    'episode': 12
                },
            ]

        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from data_source
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise Exception
