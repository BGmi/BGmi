# coding=utf-8
import os.path
import re
import time
from collections import defaultdict
from copy import deepcopy
from itertools import chain
from typing import List, Dict, Iterator, Union, Callable
import imghdr
import requests
from fuzzywuzzy import fuzz
from hanziconv import HanziConv

from bgmi.config import MAX_PAGE, ENABLE_GLOBAL_FILTER, GLOBAL_FILTER
from bgmi.lib.models import Bangumi, Filter, BangumiItem, db, STATUS_UPDATING, model_to_dict, Subtitle, STATUS_FOLLOWED, STATUS_UPDATED, Followed
from bgmi.utils import test_connection, print_warning, print_info, download_cover, convert_cover_url_to_path
from bgmi.website.bangumi_moe import BangumiMoe
from bgmi.website.mikan import Mikanani
from bgmi.website.share_dmhy import DmhySource

DATA_SOURCE_MAP = {
    'mikan_project': Mikanani(),
    'bangumi_moe': BangumiMoe(),
    'dmhy': DmhySource(),
}


def FullToHalf(s):
    n = []
    # s = s.decode('utf-8')
    for char in s:
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:
            num -= 0xfee0
        num = chr(num)
        n.append(num)
    return ''.join(n)


def similarity_of_two_name(name1: str, name2: str):
    name1 = HanziConv.toSimplified(name1)
    name2 = HanziConv.toSimplified(name2)
    name1 = FullToHalf(name1)
    name2 = FullToHalf(name2)
    name1 = name1.lower()
    name2 = name2.lower()
    if name1 in name2:
        return 100
    if name2 in name1:
        return 100
    name1_start = name1[:min(5, len(name1))]
    if name2.startswith(name1_start):
        return 100

    return fuzz.ratio(name1, name2)

class BangumiList(list):
    """
    a list of bgmi.lib.models.Bangumi
    """
    threshold = 60
    # __getitem__: Callable[[int], Bangumi]

    def append(self, obj):
        if not isinstance(obj, Bangumi):
            raise ValueError("BangumiList's item must be a instance of Bangumi")
        super().append(obj)

    def __setitem__(self, key, value):
        if not isinstance(value, Bangumi):
            raise ValueError("BangumiList's item must be a instance of Bangumi")
        super().__setitem__(key, value)

    def __init__(self, iterator=None):
        if iterator is not None:
            for i, item in enumerate(iterator):
                if not isinstance(item, Bangumi):
                    item = Bangumi(**item)
                    iterator[i] = item
                if not item.data_source:
                    item.data_source = {}
                if not item.subject_name:
                    item.subject_name = item.name
            super(BangumiList, self).__init__(iterator)
        else:
            super(BangumiList, self).__init__()

    def has_this_subject_id_as_mainline(self, subject_id: str) -> bool:
        return bool([x for x in self if x.subject_id == subject_id])

    def to_dict(self):
        e = [model_to_dict(x) for x in self]
        for item in e:
            for data_source_key in item['data_source']:
                if not isinstance(item['data_source'][data_source_key], dict):
                    item['data_source'][data_source_key] = model_to_dict(item['data_source'][data_source_key])
        return e

    def merge_another_bangumi_list(self, source: str, another_bangumi_list: List, ):
        for item in another_bangumi_list:
            self.add_bangumi(source, item, set_status=STATUS_UPDATING)

    def add_mainline_dict(self, bangumi: Dict[str, Union[List, str]]):
        b = Bangumi(**bangumi)
        self.add_mainline(b)

    def add_mainline(self, bangumi: Bangumi):
        similarity, similar_index = self.find_most_similar_index(bangumi.name)  # type: int, int
        if similarity > self.threshold:

            data_source = {key: BangumiItem(**model_to_dict(value)) if isinstance(value, BangumiItem) else BangumiItem(**value)
                           for key, value in self[similar_index].data_source.items()}
            s = [x.name for x in data_source.values()] + [bangumi.name, ]
            self[similar_index] = Bangumi(id=self[similar_index].id,
                                          name=self[similar_index].name,
                                          cover=bangumi.cover,
                                          status=STATUS_UPDATING,
                                          subject_name=bangumi.name,
                                          bangumi_names=set(s),
                                          subject_id=bangumi.subject_id,
                                          update_time=bangumi.update_time,
                                          subtitle_group=None,
                                          data_source=data_source)

        else:
            b = Bangumi(name=bangumi.name,
                        cover=bangumi.cover,
                        status=bangumi.status,
                        subject_name=bangumi.name,
                        bangumi_names={bangumi.name},
                        subject_id=bangumi.subject_id,
                        update_time=bangumi.update_time,
                        subtitle_group=None,
                        data_source={})
            self.append(b)

    def find_most_similar_index(self, name, mainline=False, data_source=None):
        if not self:
            return 0, None
        similarity_list = list(map(lambda x: similarity_of_two_name(name, x.subject_name), self))
        while True:
            max_similarity = max(similarity_list)
            most_similar_index = similarity_list.index(max_similarity)
            if not mainline:
                return max_similarity, most_similar_index
            else:
                if self[most_similar_index].get('subject_id'):
                    similarity_list[most_similar_index] = 0
                else:
                    return max_similarity, most_similar_index

    def add_bangumi(self, source: str, bangumi: Union[dict, BangumiItem, Bangumi], set_status=None):
        if isinstance(bangumi, BangumiItem) or isinstance(bangumi, Bangumi):
            bangumi = model_to_dict(bangumi)
        similarity_list = list(map(lambda x: similarity_of_two_name(bangumi['name'], x.subject_name), self))
        max_similarity = max(similarity_list)

        if max_similarity > self.threshold:
            most_similar_index = similarity_list.index(max_similarity)
            self[most_similar_index].add_data_source(source, deepcopy(bangumi))
            self[most_similar_index].bangumi_names.add(bangumi['name'])
            if set_status is not None:
                self[most_similar_index].status = set_status

        # add as mainline
        else:
            bangumi_deep_copy = {
                "name": bangumi['name'],
                "cover": bangumi['cover'],
                "status": STATUS_UPDATING,
                "subject_id": None,  # bangumi id
                "bangumi_names": {bangumi['name']},
                "subject_name": bangumi['name'],
                "update_time": bangumi['update_time'],
                'data_source': {
                    source: BangumiItem(**deepcopy(bangumi))
                }
            }
            if set_status is not None:
                bangumi_deep_copy['status'] = set_status

            self.append(Bangumi(**bangumi_deep_copy))

    @classmethod
    def from_list_of_model(cls, bangumi_list: List[BangumiItem], source):
        l = []
        for item in bangumi_list:
            d = model_to_dict(item)
            d['data_source'] = {source: deepcopy(item)}
            l.append(
                Bangumi(**d)
            )
        return cls(l)

    # @classmethod
    # def from_list_of_dict(cls, bangumi_list: List[dict], source):
    #     for i, item in enumerate(bangumi_list):
    #         e[i] = Bangumi(
    #             data_source={source: deepcopy(item)},
    #             **item
    #         )
    #     return cls(bangumi_list)

    def add_data_source_bangumi_list(self, bangumi_list: List[Union[dict, Bangumi]], source):
        for bangumi in bangumi_list:
            self.add_bangumi(source, bangumi, set_status=STATUS_UPDATING)

    def to_weekly_list(self):
        result_group_by_weekday = defaultdict(list)
        for bangumi in self.to_dict():
            result_group_by_weekday[bangumi['update_time'].lower()].append(bangumi)
            return result_group_by_weekday
        return result_group_by_weekday

def format_bangumi_dict(bangumi):
    """

    :type bangumi: dict
    """
    # return bangumi
    return {
        "name": bangumi['name'],
        "cover": bangumi['cover'],
        "status": bangumi['status'],
        "keyword": bangumi['keyword'],  # bangumi id
        "update_time": bangumi['update_time'],
        "subtitle_group": bangumi['subtitle_group'],
    }


def get_bgm_tv_calendar() -> BangumiList:
    r = requests.get('https://api.bgm.tv/calendar')
    r = r.json()
    bangumi_tv_weekly_list = BangumiList()

    for day in r:
        for index, item in enumerate(day['items']):
            if item['name_cn']:
                name = item['name_cn']
            else:
                name = item['name']
            images = item.get('images', {})
            # day['items'][index] = \
            bangumi_tv_weekly_list.append(Bangumi(
                name=name,
                cover=images.get("large", images.get('common')),
                status=STATUS_UPDATING,
                subject_id=item['id'],
                update_time=day['weekday']['en'].capitalize(),
                subject_name=name,
                data_source={},
            ))
    return bangumi_tv_weekly_list


def init_data() -> (Dict[str, list], Dict[str, list]):
    bangumi = {}  # type: Dict[str, List[BangumiItem]]
    subtitle = {}

    for data_source_id, data_source in DATA_SOURCE_MAP.items():
        # print_info('Fetching {}'.format(data_source_id))
        try:
            bangumi[data_source_id], subtitle[data_source_id] = data_source.get_bangumi_calendar_and_subtitle_group()
        except requests.ConnectionError:
            print_warning('Fetch {} failure'.format(data_source_id))
    return bangumi, subtitle


class DataSource:
    class Utils:

        @staticmethod
        def remove_duplicated_bangumi(result):
            """

            :type result: list[dict]
            """
            ret = []
            episodes = list({i['episode'] for i in result})
            for i in result:
                if i['episode'] in episodes:
                    ret.append(i)
                    del episodes[episodes.index(i['episode'])]

            return ret

        @staticmethod
        def filter_keyword(data, regex=None):
            """

            :type regex: str
            :param data: list of bangumi dict
            :type data: list[dict]
            """
            if regex:
                try:
                    match = re.compile(regex)
                    data = [s for s in data if match.findall(s['title'])]
                except re.error as exc:
                    if os.getenv('DEBUG'):  # pragma: no cover
                        import traceback

                        traceback.print_exc()
                        raise exc
                    return data

            return data

    def fetch(self, save=False, group_by_weekday=True):
        bangumi_result, subtitle_group_result = init_data()

        bangumi_name_list = []
        for data_source_id, data in bangumi_result.items():
            bangumi_name_list += [x['name'] for x in data]

        bgm_tv_weekly_list = get_bgm_tv_calendar()
        bangumi_name_list += [x.name for x in bgm_tv_weekly_list]
        bangumi_name_list = list(set(bangumi_name_list))

        bangumi_calendar = BangumiList(Bangumi.select())

        tmp_bangumi_calendar = set()

        for bangumi in bangumi_calendar:
            for name in bangumi_name_list:
                if name in bangumi.bangumi_names:
                    tmp_bangumi_calendar.add(bangumi)

        bangumi_calendar = BangumiList(tmp_bangumi_calendar)


        for item in bgm_tv_weekly_list:
            bangumi_calendar.add_mainline(item)

        for data_source_id, data in bangumi_result.items():
            for item in data:
                bangumi_calendar.add_bangumi(source=data_source_id, bangumi=item, set_status=STATUS_UPDATING)

        bangumi_calendar = BangumiList([x for x in bangumi_calendar if x.data_source])
        Bangumi.delete_all()
        Subtitle.save_subtitle_list(subtitle_group_result)

        if not bangumi_result:
            print('no result return None')
            return []

        if save:
            with db.atomic():
                for bangumi in bangumi_calendar:
                    self.save_data(bangumi)

        if group_by_weekday:
            result_group_by_weekday = defaultdict(list)
            for bangumi in bangumi_calendar.to_dict():
                result_group_by_weekday[bangumi['update_time'].lower()].append(bangumi)
            return result_group_by_weekday

        return bangumi_calendar.to_dict()

    @staticmethod
    def save_data(data: Bangumi):
        """
        save bangumi dict to database

        # :type data: dict
        """

        def to_d(field):
            return {key: model_to_dict(value) for key, value in dict(field).items()}

        b, obj_created = Bangumi.get_or_create(name=data.name, defaults=model_to_dict(data, recurse=True))  # type: (Bangumi, bool)
        if not obj_created:
            if (
                b.cover != data.cover or
                b.status != data.status or
                b.subject_id != data.subject_id or
                b.update_time != data.update_time or
                b.subject_name != data.subject_name or
                set(set(b.bangumi_names) - set(data.bangumi_names)) or
                to_d(b.data_source) != to_d(b.data_source)
            ):

                b.cover = data.cover
                b.status = data.status
                b.subject_id = data.subject_id
                b.update_time = data.update_time
                b.bangumi_names = data.bangumi_names
                b.data_source = data.data_source
                b.subject_name = data.subject_name
                b.save()

        # data.save()

    def bangumi_calendar(self, force_update=False, save=True, cover=None):
        """

        :param force_update:
        :type force_update: bool

        :param save: set true to enable save bangumi data to database
        :type save: bool

        :param cover: list of cover url (of scripts) want to download
        :type cover: bool
        """
        if force_update and not test_connection():
            force_update = False
            print_warning('Network is unreachable')

        if force_update:
            print_info('Fetching bangumi info ...')
            weekly_list = self.fetch(save=save)
        else:
            weekly_list = Bangumi.get_updating_bangumi()

        if not weekly_list:
            print_warning('Warning: no bangumi schedule, fetching ...')
            weekly_list = self.fetch(save=save)

        if cover is not None:
            # download cover to local
            cover_to_be_download = []
            for daily_bangumi in weekly_list.values():
                for bangumi in daily_bangumi:
                    _, file_path = convert_cover_url_to_path(bangumi['cover'])
                    if not (os.path.exists(file_path) and imghdr.what(file_path)):
                        cover_to_be_download.append(bangumi['cover'])

            if cover_to_be_download:
                print_info('Updating cover ...')
                download_cover(cover_to_be_download)

        return weekly_list

    def get_maximum_episode(self, bangumi, subtitle=True, ignore_old_row=True, max_page=int(MAX_PAGE)):
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
        followed_filter_obj, _ = Filter.get_or_create(bangumi_name=bangumi.name)  # type : (Filter, bool)

        data = [i for i in self.fetch_episode(bangumi_obj=bangumi,
                                              filter_obj=followed_filter_obj,
                                              max_page=int(max_page))
                if i['episode'] is not None]

        if ignore_old_row:
            data = [row for row in data if row['time'] > int(time.time()) - 3600 * 24 * 30 * 3]  # three month

        if data:
            bangumi = max(data, key=lambda _i: _i['episode'])
            return bangumi, data
        else:
            return {'episode': 0}, []

    def fetch_episode(self,
                      filter_obj: Filter = None,
                      bangumi_obj=None,
                      max_page=int(MAX_PAGE)):
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
        result = []
        _id = bangumi_obj.id
        name = bangumi_obj.name
        max_page = int(max_page)

        if filter_obj.data_source:
            source = list(set(bangumi_obj.data_source.keys()) & set(filter_obj.data_source))
        else:
            source = list(bangumi_obj.data_source.keys())

        response_data = []

        if filter_obj.subtitle:
            subtitle_group = Subtitle.select(Subtitle.id, Subtitle.data_source) \
                .where(Subtitle.name.in_(filter_obj.subtitle) & Subtitle.data_source.in_(source))

            condition = defaultdict(list)

            for subtitle in subtitle_group:
                condition[subtitle.data_source].append(subtitle.id)

            for s, subtitle_group in condition.items():
                print_info('Fetching {}'.format(s))
                response_data += DATA_SOURCE_MAP[s].fetch_episode_of_bangumi(
                    bangumi_id=bangumi_obj.data_source[s]['keyword'],
                    subtitle_list=subtitle_group,
                    max_page=max_page
                )

        else:
            for s in source:
                print_info('Fetching {}'.format(s))
                response_data += DATA_SOURCE_MAP[s].fetch_episode_of_bangumi(
                    bangumi_id=bangumi_obj.data_source[s]['keyword'],
                    max_page=max_page
                )

        result = response_data
        filter_obj.exclude.append('合集')

        if not ENABLE_GLOBAL_FILTER == '0':
            filter_obj.exclude += [x.strip() for x in GLOBAL_FILTER.split(',')]

        if filter_obj.include:
            f = lambda s: all(map(lambda t: t in s['title'], filter_obj.include))
            result = list(filter(f, result))

        if filter_obj.exclude:
            f = lambda s: not any(map(lambda t: t in s['title'], filter_obj.exclude))
            result = list(filter(f, result))

        if filter_obj.regex:
            result = self.Utils.filter_keyword(data=result, regex=filter_obj.regex)

        return result

    @staticmethod
    def followed_bangumi():
        """

        :return: list of bangumi followed
        :rtype: list[dict]
        """
        weekly_list_followed = Bangumi.get_updating_bangumi(status=STATUS_FOLLOWED)
        weekly_list_updated = Bangumi.get_updating_bangumi(status=STATUS_UPDATED)
        weekly_list = defaultdict(list)
        for k, v in chain(weekly_list_followed.items(), weekly_list_updated.items()):
            weekly_list[k].extend(v)
        for bangumi_list in weekly_list.values():
            for bangumi in bangumi_list:
                bangumi['subtitle_group'] = [{'name': x['name'],
                                              'id': x['id']} for x in
                                             Subtitle.get_subtitle_from_data_source_dict(bangumi['data_source'])]
        return weekly_list

    def search_by_keyword(self, keyword, count):  # pragma: no cover
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
        return sum([print_info('Search in {}'.format(i)) or s.search_by_keyword(keyword, count) for i, s in
                    DATA_SOURCE_MAP.items()], [])


if __name__ == '__main__':
    website = DataSource()
    website.fetch()
