from unittest import mock, TestCase

from bgmi.website import DataSource
from bgmi.website.base import BaseWebsite

w = lambda: mock.Mock(spec=BaseWebsite)

# from .mock_websites import MockDateSource
from tests.mock_websites import MockDateSource


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

    def test_get_maximum_episode(self):
        """
        """
        raise Exception

    def test_fetch_episode(self):
        """
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
