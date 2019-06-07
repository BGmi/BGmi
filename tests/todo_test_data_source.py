from unittest import TestCase, mock

from bgmi.website import DataSource
from bgmi.website.base import BaseWebsite
# from .mock_websites import MockDateSource
from tests.mock_websites import MockDateSource


def w():
    return mock.Mock(spec=BaseWebsite)


@mock.patch('bgmi.website.DATA_SOURCE_MAP', MockDateSource)
class TestDataSourceUtils(TestCase):
    def test_remove_duplicated_bangumi(self):
        duplicated_episode = [{
            'title': 'bangumi',
            'episode': 1,
        }, {
            'title': 'bangumi',
            'episode': 1,
        }, {
            'title': 'bangumi',
            'episode': 2,
        }]
        e = DataSource.Utils.remove_duplicated_episode_bangumi(duplicated_episode)
        self.assertEqual(len(e), 2)
        self.assertListEqual(e, [duplicated_episode[0], duplicated_episode[-1]])


@mock.patch('bgmi.website.DATA_SOURCE_MAP', MockDateSource)
# class TestDataSource(TestCase):
class TestDataSource:
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
        :param count: how many page to fetch from data_source_id
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise Exception
