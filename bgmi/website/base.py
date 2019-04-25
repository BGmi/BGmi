from abc import ABC, abstractmethod

from bgmi.config import MAX_PAGE
from bgmi.lib.models import BangumiItem
from bgmi.utils import normalize_path, parse_episode


class BaseWebsite(ABC):
    cover_url = ''
    source_id = ''
    parse_episode = staticmethod(parse_episode)

    def get_bangumi_calendar_and_subtitle_group(self):
        bangumi_result, subtitile_result = self.fetch_bangumi_calendar_and_subtitle_group()
        for item in bangumi_result:
            item['cover'] = self.cover_url + item['cover']
            item['name'] = normalize_path(item['name'])
        # for i, bangumi in enumerate(bangumi_result):
        #     bangumi_result[i] = Bangumi(**bangumi)
        bangumi_result = [
            BangumiItem(**bangumi) for bangumi in bangumi_result if bangumi['subtitle_group']
        ]
        return bangumi_result, subtitile_result

    @abstractmethod
    def fetch_bangumi_calendar_and_subtitle_group(self):  # pragma: no cover
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        example:
        ```
            [
                {
                    "status": 0,
                    "subtitle_group": [
                        "123",
                        "456"
                    ],
                    "name": "名侦探柯南",
                    "keyword": "1234", #bangumi id
                    "update_time": "Sat",
                    "cover": "data/images/cover1.jpg"
                },
            ]
        ```

        list of subtitle group dict:
        example:
        ```
            [
                {
                    'id': '233',
                    'name': 'bgmi字幕组'
                }
            ]
        ```


        :return: list of bangumi, list of subtitile group
        :rtype: (list[dict], list[dict])
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_episode_of_bangumi(
        self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE
    ):  # pragma: no cover
        """
        get all episode by bangumi id
        example
        ```
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
                    "subtitle_group": "58a9c1c9f5dc363606ab42ec",
                    "title": "【喵萌奶茶屋】★七月新番★[来自深渊/Made in Abyss][07][GB][720P]",
                    "episode": 0,
                    "time": 1503301292
                },
            ]
        ```

        :param bangumi_id: bangumi_id
        :param subtitle_list: list of subtitle group
        :type subtitle_list: list
        :param max_page: how many page you want to crawl if there is no subtitle list
        :type max_page: int
        :return: list of bangumi
        :rtype: list[dict]
        """
        raise NotImplementedError

    @abstractmethod
    def search_by_keyword(self, keyword, count=None):
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
        ```
        :param keyword: search key word
        :type keyword: str
        :param count: how many page to fetch from website
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise NotImplementedError
