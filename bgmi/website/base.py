from abc import ABC, abstractmethod
from typing import List, Tuple

from bgmi.models import DataSourceItem, Subtitle
from bgmi.utils import parse_episode


class BaseWebsite(ABC):
    cover_url = ''
    """
    cover url base. bangumi cover url will be
    """
    parse_episode = staticmethod(parse_episode)

    def get_bangumi_calendar_and_subtitle_group(
        self
    ) -> Tuple[List[DataSourceItem], List[Subtitle]]:
        bangumi_result, subtitile_result = self.fetch_bangumi_calendar_and_subtitle_group()
        # for item in bangumi_result:
        #     item['name'] = normalize_path(item['name'])
        bangumi_result = [
            DataSourceItem(
                data_source_id=self.data_source_id,
                **bangumi,
            ) for bangumi in bangumi_result if bangumi['subtitle_group']
        ]
        return bangumi_result, [
            Subtitle(data_source_id=self.data_source_id, **x) for x in subtitile_result
        ]

    @property
    @abstractmethod
    def name(self):
        """
        return bangumi source name

        :rtype: str
        """

    @property
    @abstractmethod
    def data_source_id(self):
        """
        id of this data source, should be same with its entry point

        :rtype: str
        """

    @abstractmethod
    def fetch_bangumi_calendar_and_subtitle_group(self):  # pragma: no cover
        """
        return a list of all bangumi and a list of all subtitle group

        list of bangumi dict:
        update time should be one of ``['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']``
        (``bgmi.lib.db_models._tables.Bangumi.week``)

        .. warning::

            cover should starts with ``http://`` or ``https://``

        .. code-block:: python

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
                    "cover": "https://www.example.com/data/images/cover1.jpg"
                },
            ]

        list of subtitle group dict:

        .. code-block:: python

            [
                {
                    'id': '233',
                    'name': 'bgmi字幕组'
                }
            ]


        :return: list of bangumi, list of subtitile group
        :rtype: (list[dict], list[dict])
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_episode_of_bangumi(self,
                                 bangumi_id,
                                 max_page,
                                 subtitle_list=None) -> List[dict]:  # pragma: no cover
        """
        get all episode by bangumi id
        example

        .. code-block:: python
            [
                {
                    "download": "magnet:?xt=urn:btih:e43b3b6b53dd9fd6af1199e112d3c7ff15cab82c",
                    "subtitle_group": "58a9c1c9f5dc363606ab42ec",
                    "title": "【喵萌奶茶屋】★七月新番★[来自深渊/Made in Abyss][07][GB][720P]",
                    "episode": 0,
                    "time": 1503301292
                },
            ]

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
        search torrent by arguments.
        return a list of dict with at least 4 key: download, name, title, episode.
        Other keys are omitted.

        .. code-block:: python

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
        :param count: how many page to fetch from website
        :type count: int

        :return: list of episode search result
        :rtype: list[dict]
        """
        raise NotImplementedError
