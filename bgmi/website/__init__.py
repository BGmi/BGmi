import html
import ssl
import time
from collections import defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from itertools import chain
from typing import DefaultDict, Iterator, List, Tuple

import requests
import stevedore
from hanziconv import HanziConv

import bgmi
from bgmi import config, models
from bgmi.config import MAX_PAGE
from bgmi.lib.constants import NameSpace
from bgmi.lib.db_models import (
    Bangumi, BangumiItem, Followed, Subtitle, db, get_updating_bangumi_with_data_source,
    get_updating_bangumi_with_out_data_source
)
from bgmi.models.status import BangumiStatus
from bgmi.utils import full_to_half, normalize_path, parallel, print_info, print_warning
from bgmi.website.base import BaseWebsite

from . import bangumi_moe, base, mikan, share_dmhy

THRESHOLD = 60
_MAX_PAGE: int = int(MAX_PAGE)


def _raise(_1, _2, c):
    raise c


@lru_cache(20)
def get_provider(source) -> BaseWebsite:
    return stevedore.DriverManager(
        namespace=NameSpace.data_source_provider,
        name=source,
        invoke_on_load=True,
        on_load_failure_callback=_raise,
    ).driver


def get_all_provider() -> Iterator[Tuple[str, BaseWebsite]]:
    mgr = stevedore.ExtensionManager(
        namespace=NameSpace.data_source_provider,
        invoke_on_load=True,
        on_load_failure_callback=_raise,
    )
    yield from [(source_id, ext.obj) for (source_id, ext) in mgr.items()]


def similarity_of_two_name(name1: str, name2: str):
    name1 = HanziConv.toSimplified(name1)
    name2 = HanziConv.toSimplified(name2)
    name1 = full_to_half(name1)
    name2 = full_to_half(name2)
    name1 = name1.lower()
    name2 = name2.lower()
    if name1 in name2:
        return 100
    if name2 in name1:
        return 100
    name1_start = name1[:min(5, len(name1))]
    if name2.startswith(name1_start):
        return 100
    return int(SequenceMatcher(None, name1, name2).ratio() * 100)


def format_bangumi_dict(bangumi):
    """

    :type bangumi: dict
    """
    # return bangumi
    return {
        'name': bangumi['name'],
        'cover': bangumi['cover'],
        'status': bangumi['status'],
        'keyword': bangumi['keyword'],  # bangumi id
        'update_time': bangumi['update_time'],
        'subtitle_group': bangumi['subtitle_group'],
    }


def get_bgm_tv_calendar() -> list:
    # bgm.tv now checks request User-Agent, and using default requests UA will be blocked
    req = requests.get(
        'https://api.bgm.tv/calendar',
        headers={'user-agent': f'BGmi/{bgmi.__version__} https://github.com/BGmi/BGmi'}
    )
    r: dict = req.json()
    bangumi_tv_weekly_list = []

    for day in r:
        for item in day['items']:
            if item['name_cn']:
                name = item['name_cn']
            else:
                name = item['name']
            images = item.get('images')
            if not images:
                images = {}
            # day['items'][index] = \
            bangumi_tv_weekly_list.append(
                models.Bangumi(
                    name=normalize_path(html.unescape(name)),
                    cover=images.get('large', images.get('common')) or '',
                    status=BangumiStatus.UPDATING,
                    subject_id=item['id'],
                    update_time=day['weekday']['en'].capitalize(),
                    data_source={},
                )
            )
    return bangumi_tv_weekly_list


def init_data() -> Tuple[List[models.DataSourceItem], List[models.Subtitle]]:
    bangumi_list = []
    subtitle_list = []

    for data_source_id, data_source in get_all_provider():
        if data_source_id in config.DISABLED_DATA_SOURCE:
            continue
        print_info(f'Fetching {data_source_id}')
        try:
            _bangumi, _subtitle = data_source.get_bangumi_calendar_and_subtitle_group()
            bangumi_list.extend(_bangumi)
            subtitle_list.extend(_subtitle)
        except requests.ConnectionError:
            print_warning(f'Fetch {data_source_id} failure')
        except ssl.SSLError:
            print_warning(f'Fetch {data_source_id} failure')
    return bangumi_list, subtitle_list


class DataSource:
    class Utils:
        @staticmethod
        def remove_duplicated_episode_bangumi(result: List[models.Episode]) -> List[models.Episode]:
            ret = []
            episodes = list({i.episode for i in result})
            for i in result:
                if i.episode in episodes:
                    ret.append(i)
                    del episodes[episodes.index(i.episode)]

            return ret

    def fetch(self, save=False, group_by_weekday=True):
        # get all bangumi item
        bgm_tv_weekly_list = get_bgm_tv_calendar()
        bangumi_result, subtitle_group_result = init_data()

        # save bangumi item and data source to db
        if save:
            with db.atomic():
                Subtitle.save_subtitle_list(subtitle_group_result)
                for bangumi in bangumi_result:
                    self.save_data_bangumi_item(bangumi)

        for item in bgm_tv_weekly_list:
            self.save_data(item)

        bind_bangumi_item_in_db_to_bangumi()

        bangumi_result = get_updating_bangumi_with_out_data_source(order=group_by_weekday)
        if not bangumi_result:
            print('no result return None')
            return defaultdict(list)
        return bangumi_result

    @staticmethod
    def save_data(data: models.Bangumi):
        """
        save bangumi dict to database

        # :type data: dict
        """
        b, obj_created = Bangumi.get_or_create(
            subject_id=data.subject_id, defaults=data.dict()
        )  # type: (Bangumi, bool)
        if not obj_created:
            if b != data:
                b.name = data.name
                b.cover = data.cover
                b.status = data.status
                b.update_time = data.update_time
                b.save()

    @staticmethod
    def save_data_bangumi_item(data: models.DataSourceItem):
        """
        save bangumi dict to database

        # :type data: dict
        """
        d = data.copy()
        d.subtitle_group = ','.join(data.subtitle_group)  # type: ignore
        b, obj_created = BangumiItem.get_or_create(
            keyword=data.keyword, data_source_id=data.data_source_id, defaults=d.dict()
        )  # type: (BangumiItem, bool)

        if not obj_created:
            if b != d:
                b.cover = d.cover
                b.status = d.status
                b.update_time = d.update_time
                b.subtitle_group = d.subtitle_group
                b.save()

    def bangumi_calendar(self, force_update=False, save=True, detail=False):
        """

        :param detail:
        :type detail: bool
        :param force_update:
        :type force_update: bool

        :param save: set true to enable save bangumi data to database
        :type save: bool
        """
        if force_update:
            print_info('Fetching bangumi info ...')
            weekly_list = self.fetch(save=save)
        else:
            if detail:
                weekly_list = get_updating_bangumi_with_data_source()
            else:
                weekly_list = get_updating_bangumi_with_out_data_source()

        if not weekly_list:
            print_warning('Warning: no bangumi schedule, fetching ...')
            weekly_list = self.fetch(save=save)

        return weekly_list

    def get_maximum_episode(self,
                            bangumi,
                            ignore_old_row=True,
                            max_page=_MAX_PAGE) -> Tuple[dict, List[models.Episode]]:
        """

        :type max_page: str
        :param max_page:
        :type bangumi: object
        :type ignore_old_row: bool
        :param ignore_old_row:
        :type bangumi: bgmi.lib.db_models._tables.Bangumi
        """
        followed_filter_obj, _ = Followed.get_or_create(
            bangumi_id=bangumi.id
        )  # type : (Filter, bool)

        data = [
            i for i in self.fetch_episode(
                filter_obj=models.Followed.parse_db_models(followed_filter_obj),
                bangumi_obj=bangumi,
                max_page=int(max_page),
            ) if i.episode is not None
        ]

        if ignore_old_row:
            data = [
                row for row in data if row.time > int(time.time()) - 3600 * 24 * 30 * 3
            ]  # three month

        if data:
            ep_info = max(data, key=lambda _i: _i.episode)

            return {'episode': ep_info.episode}, data
        return {'episode': 0}, []

    @staticmethod
    def fetch_episode(filter_obj: models.Followed, bangumi_obj: Bangumi,
                      max_page) -> List[models.Episode]:
        response_data: List[dict] = []

        available_source: List[BangumiItem] = []
        for x in BangumiItem.select_by_bangumi_id(bangumi_obj.id):
            if enabled_data_source_id(x.data_source_id, filter_obj):
                available_source.append(x)

        bangumi_items = {}

        for item in available_source:
            bangumi_items[item.data_source_id] = item

        available_source_ids = [x.data_source_id for x in available_source]

        if filter_obj.data_source:
            source = list(set(available_source_ids) & set(filter_obj.data_source))
        else:
            source = available_source_ids

        if filter_obj.subtitle:
            subtitle_group = Subtitle.select_by_name_and_data_source(filter_obj.subtitle, source)

            data_source_to_subtitle_group: DefaultDict[str, set] = defaultdict(set)

            for subtitle in subtitle_group:
                data_source_to_subtitle_group[subtitle.data_source_id].add(subtitle.id)
            for item in available_source:
                print_info(f'Fetching {item.name} from {item.data_source_id}')
                # driver.driver
                response_data += get_provider(item.data_source_id).fetch_episode_of_bangumi(
                    bangumi_id=item.keyword,
                    subtitle_list=list(data_source_to_subtitle_group[item.data_source_id]),
                    max_page=max_page,
                )

        else:
            for source in available_source:
                print_info(f'Fetching {bangumi_obj.name} from {source.data_source_id}')
                response_data += get_provider(
                    source.data_source_id
                ).fetch_episode_of_bangumi(bangumi_id=source.keyword, max_page=max_page)
        for episode in response_data:
            episode['name'] = bangumi_obj.name

        return filter_obj.apply_keywords_filter_on_list_of_episode([
            models.Episode(**x) for x in response_data
        ])

    @staticmethod
    def followed_bangumi():
        """

        :return: list of bangumi followed
        :rtype: list[dict]
        """
        weekly_list_followed = Bangumi.get_updating_bangumi(status=Followed.STATUS.FOLLOWED)
        weekly_list_updated = Bangumi.get_updating_bangumi(status=Followed.STATUS.UPDATED)
        weekly_list = defaultdict(list)
        for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
            weekly_list[k].extend(v)
        for bangumi_list in weekly_list.values():
            for bangumi in bangumi_list:
                bangumi['subtitle_group'] = [{
                    'name': x['name'], 'id': x['id']
                } for x in Subtitle.get_subtitle_from_data_source_dict(bangumi)]
        return weekly_list

    @staticmethod
    def search_by_keyword(keyword, count):  # pragma: no cover
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
        def f(_, source):
            return [models.Episode.parse_obj(x) for x in source.search_by_keyword(keyword, count)]

        return sum(parallel(f, get_all_provider()), [])


def find_most_similar_index(container, name):
    if not container:
        return 0, None
    similarity_list = [similarity_of_two_name(name, x.name) for x in container]
    max_similarity = max(similarity_list)
    most_similar_index = similarity_list.index(max_similarity)
    return max_similarity, most_similar_index


def bind_bangumi_item_in_db_to_bangumi():
    bangumi_item_list = list(BangumiItem.get_unmarked_updating_bangumi())
    bangumi_list = list(Bangumi.get_updating_bangumi(order=False, obj=True))
    for bangumi in bangumi_item_list:
        value, index = find_most_similar_index(bangumi_list, bangumi.name)
        if value > THRESHOLD:
            bangumi.bangumi_id = bangumi_list[index].id
            bangumi_list[index].has_data_source = 1
            bangumi_list[index].save()
            bangumi.save()

    bangumi_item_list = list(BangumiItem.get_marked_updating_bangumi())
    Bangumi.update(has_data_source=1).where(
        Bangumi.id.in_([x.bangumi_id for x in bangumi_item_list])
        & (Bangumi.status == Bangumi.STATUS.UPDATING)
    ).execute()
    Bangumi.update(has_data_source=0).where(
        Bangumi.id.not_in([x.bangumi_id for x in bangumi_item_list])
        & (Bangumi.status == Bangumi.STATUS.UPDATING)
    ).execute()


def enabled_data_source_id(data_source_id, followed: models.Followed):

    if data_source_id in config.DISABLED_DATA_SOURCE:
        return False
    if Followed and followed.data_source:
        if data_source_id in followed.data_source:
            return False
    return True


__all__ = [
    'mikan',
    'bangumi_moe',
    'share_dmhy',
    'base',
    'DataSource',
    'bind_bangumi_item_in_db_to_bangumi',
    'get_all_provider',
    'get_provider',
]
