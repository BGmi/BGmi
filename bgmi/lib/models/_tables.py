import hashlib
import json
import os
import re
import time
from collections import defaultdict
from enum import IntEnum
from typing import Dict, Iterator, List, Union

import peewee as pw
from playhouse.shortcuts import model_to_dict

import bgmi.config
from bgmi.lib.constants import SECOND_OF_WEEK

from ._db import NeoDB, db
from ._fields import BangumiNamesField, SubtitleField


class BangumiItem(pw.Model):
    """
    This model is the item of Bangumi.data_source:Dict[str, BangumiItem]

    It will not be stored in database and there isn't a table named BangumiItem in database.
    """

    class Meta:
        table_name = 'bangumi_item'
        database = db
        indexes = (
            # create a unique on from/to/date
            (('keyword', 'data_source'), True),
        )
        # primary_key = pw.CompositeKey('keyword', 'data_source')

    id = pw.AutoField(primary_key=True)
    name = pw.CharField()  # type: str
    cover = pw.CharField()  # type: str
    status = pw.IntegerField()  # type: int
    update_time = pw.FixedCharField(5, null=False)  # type: str
    subtitle_group = SubtitleField()  # type: List[str]
    keyword = pw.CharField()  # type: str
    data_source = pw.FixedCharField(max_length=30)  # type: str
    # foreign key
    bangumi = pw.IntegerField(default=0)

    class STATUS(IntEnum):
        UPDATING = 0
        END = 1

    def __getitem__(self, item):
        return getattr(self, item)

    def __init__(self, *args, **kwargs):
        if isinstance(kwargs.get('subtitle_group'), str):
            kwargs['subtitle_group'] = [x.strip() for x in kwargs['subtitle_group'].split(',')]
        super().__init__(*args, **kwargs)
        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in Bangumi.week:
            raise ValueError('unexpected update time %s' % update_time)
        self.update_time = update_time

    def __str__(self):
        return '<BangumiItem name={}>'.format(self.name)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, data):
        return self.cover == data.cover \
            and self.status == data.status \
            and self.update_time == data.update_time \
            and set(self.subtitle_group) == set(data.subtitle_group)

    @classmethod
    def get_updating_bangumi_item(cls):
        return cls.select().where(cls.status == cls.STATUS.UPDATING)

    @classmethod
    def delete_all(cls):
        return cls.update(status=cls.STATUS.END).execute()

    @classmethod
    def get_unmarked_updating_bangumi(cls) -> Iterator['BangumiItem']:
        cond = (cls.bangumi == cls.bangumi.default) & \
               (cls.status == cls.STATUS.UPDATING)
        return cls.select().where(cond)

    @classmethod
    def get_marked_updating_bangumi(cls) -> Iterator['BangumiItem']:
        cond = (cls.bangumi != cls.bangumi.default) \
            & (cls.status == cls.STATUS.UPDATING)
        return cls.select().where(cond)

    @classmethod
    def get_data_source_by_id(cls, id) -> Iterator['BangumiItem']:
        return cls.select().where(cls.bangumi == id)


class Bangumi(NeoDB):
    """
    bangumi mainline table

    """
    id = pw.AutoField(primary_key=True)  # type: Union[int, pw.AutoField]
    name = pw.CharField(unique=True, null=False)  # type: Union[str, pw.CharField]
    cover = pw.CharField(default='')
    status = pw.IntegerField(default=0)  # type: int
    subject_id = pw.IntegerField(null=True)
    update_time = pw.FixedCharField(5, null=False)
    has_data_source = pw.IntegerField(default=0)

    class STATUS(IntEnum):
        UPDATING = 0
        END = 1

    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in self.week:
            raise ValueError('unexpected update time %s' % update_time)
        self.update_time = update_time

    @classmethod
    def delete_all(cls):
        un_updated_bangumi = Followed.select().where(
            Followed.updated_time > (int(time.time()) - 2 * SECOND_OF_WEEK)
        )  # type: List[Followed]
        if os.getenv('DEBUG'):  # pragma: no cover
            print('ignore updating bangumi', [x.bangumi_name for x in un_updated_bangumi])

        cls.update(status=cls.STATUS.END) \
            .where(cls.name.not_in([x.bangumi_name for x in un_updated_bangumi])) \
            .execute()  # do not mark updating bangumi as Bangumi.STATUS.END

    @classmethod
    def get_updating_bangumi(cls, status=None, order=True, obj=False) -> Dict:
        base_cond = (cls.status == cls.STATUS.UPDATING)
        query = cls.select(Followed.status, Followed.episode, cls, ) \
            .join(Followed, pw.JOIN['LEFT_OUTER'], on=(cls.name == Followed.bangumi_name))

        if status is None:
            data = query.where(base_cond)
        else:
            data = query.where(base_cond & (Followed.status == status))
        if not obj:
            data = data.dicts()

        if order:
            weekly_list = defaultdict(list)
            for bangumi_item in data:
                weekly_list[bangumi_item['update_time'].lower()].append(dict(bangumi_item))
        else:
            weekly_list = list(data)

        return weekly_list

    @classmethod
    def get_all_bangumi(cls, has_source=True):
        if has_source:
            cond = (cls.has_data_source == has_source)
        else:
            cond = None
        return cls.select().where(cond).dicts()

    def add_data_source(self, source, bangumi):
        if isinstance(bangumi, dict):
            self.data_source[source] = BangumiItem(**bangumi)
        elif isinstance(bangumi, BangumiItem):
            self.data_source[source] = bangumi
        else:
            raise ValueError(
                'data_source item must be type dict or BangumiItem,'
                ' can\'t be {} {}'.format(type(bangumi), bangumi)
            )

    def get_subtitle_of_bangumi(self) -> 'List[Subtitle]':
        return Subtitle.get_subtitle_of_bangumi(self)

    @classmethod
    def create(cls, **query):
        if not query.get('subject_name'):
            query['subject_name'] = query['name']
        return super().create(**query)

    def __str__(self):
        d = model_to_dict(self)
        return '<Bangumi {}>'.format(json.dumps(d, ensure_ascii=False))

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def to_d(field):
        return {key: model_to_dict(value) for key, value in dict(field).items()}

    def __eq__(self, data):
        return self.cover == data.cover and \
            self.name == data.name and \
            self.status == data.status and \
            self.update_time == data.update_time

    def __hash__(self):
        return int(hashlib.sha1(self.name.encode()).hexdigest(), 16) % (10**8)


class Followed(NeoDB):
    """
    Followed bangumi and filter condition
    """
    bangumi_name = pw.CharField(unique=True, primary_key=True)
    episode = pw.IntegerField(null=True, default=0)
    status = pw.IntegerField(null=True)
    updated_time = pw.IntegerField(null=True)

    # followed filter
    data_source = SubtitleField(default=[])  # type:List
    subtitle = SubtitleField(default=[])  # type:List
    include = SubtitleField(default=[])  # type:List
    exclude = SubtitleField(default=[])  # type:List
    regex = pw.CharField(null=False, default='')  # type: str

    class STATUS(IntEnum):
        DELETED = 0
        FOLLOWED = 1
        UPDATED = 2

    @classmethod
    def delete_followed(cls, batch=True):
        q = cls.delete()
        if not batch:
            if not input('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ') == 'y':
                return False

        q.execute()
        return True

    @classmethod
    def get_all_followed(cls, status=STATUS.DELETED, bangumi_status=Bangumi.STATUS.UPDATING):
        join_cond = (Bangumi.name == cls.bangumi_name)
        d = cls.select(Bangumi.name, Bangumi.update_time, Bangumi.cover, cls, cls.episode) \
            .join(Bangumi, pw.JOIN['LEFT_OUTER'], on=join_cond) \
            .where((cls.status != status) & (Bangumi.status == bangumi_status)) \
            .order_by(cls.updated_time.desc()) \
            .dicts()

        return list(d)

    def apply_keywords_filter_on_list_of_episode(self, episode_list: List[Dict]) -> List[Dict]:
        episode_list = self.apply_include(episode_list)
        episode_list = self.apply_exclude(episode_list)
        episode_list = self.apply_regex(episode_list)
        return episode_list

    def apply_include(self, episode_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.include:

            def f1(s):
                return all(map(lambda t: t in s['title'], self.include))

            episode_list = list(filter(f1, episode_list))
        return episode_list

    def apply_exclude(self, episode_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        exclude = self.exclude
        if bgmi.config.ENABLE_GLOBAL_FILTER != '0':
            exclude += [x.strip() for x in bgmi.config.GLOBAL_FILTER.split(',')]
        exclude.append('合集')

        def f2(s):
            return not any(map(lambda t: t in s['title'], exclude))

        episode_list = list(filter(f2, episode_list))
        return episode_list

    def apply_regex(self, episode_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.regex:
            try:
                match = re.compile(self.regex)
                episode_list = [s for s in episode_list if match.findall(s['title'])]
            except re.error as exc:
                if os.getenv('DEBUG'):  # pragma: no cover
                    import traceback

                    traceback.print_exc()
                    raise exc
                return episode_list
        return episode_list


class Download(NeoDB):
    name = pw.CharField(null=False)
    title = pw.CharField(null=False)
    episode = pw.IntegerField(default=0)
    download = pw.CharField()
    status = pw.IntegerField(default=0)

    class STATUS(IntEnum):
        NOT_DOWNLOAD = 0
        DOWNLOADING = 1
        DOWNLOADED = 2

    @classmethod
    def get_all_downloads(cls, status=None):
        if status is None:
            data = list(cls.select().order_by(cls.status))
        else:
            data = list(cls.select().where(cls.status == status).order_by(cls.status))

        for index, x in enumerate(data):
            data[index] = model_to_dict(x)
        return data

    def downloaded(self):
        self.status = self.STATUS.DOWNLOADED
        self.save()


class Subtitle(NeoDB):
    id = pw.CharField()
    name = pw.CharField()
    data_source = pw.CharField()

    class Meta:
        database = db
        indexes = (
            # create a unique on from/to/date
            (('id', 'data_source'), True),
        )
        primary_key = pw.CompositeKey('id', 'data_source')

    @classmethod
    def get_subtitle_of_bangumi(cls, bangumi_obj):
        """
        :type bangumi_obj: Union[Bangumi,dict]
        """
        if isinstance(bangumi_obj, dict):
            items = BangumiItem.select().where(BangumiItem.bangumi == bangumi_obj['id']).dicts()
        else:
            items = BangumiItem.select().where(BangumiItem.bangumi == bangumi_obj.id).dicts()

        data_source_dict = {}
        for item in items:
            data_source_dict[item['data_source']] = item
        return cls.get_subtitle_from_data_source_dict(data_source_dict)

    @classmethod
    def get_subtitle_from_data_source_dict(cls, data_source):
        """
        :type data_source: dict
        :param data_source:
        :return:
        """
        source = list(data_source.keys())
        condition = list()
        for s in source:
            condition.append((Subtitle.id.in_(data_source[s]['subtitle_group']))
                             & (Subtitle.data_source == s))
        if len(condition) > 1:
            tmp_c = condition[0]
            for c in condition[1:]:
                tmp_c = tmp_c | c
        elif len(condition) == 1:
            tmp_c = condition[0]
        else:
            return []
        return [model_to_dict(x) for x in Subtitle.select().where(tmp_c)]

    @classmethod
    def save_subtitle_list(cls, subtitle_group_list):
        """
        subtitle_group_list example: `tests/data/subtitle.json`
        :type subtitle_group_list: dict
        """
        for data_source_id, subtitle_group_lists in subtitle_group_list.items():
            for subtitle_group in subtitle_group_lists:
                with db.atomic():
                    s, if_created = Subtitle.get_or_create(
                        id=str(subtitle_group['id']),
                        data_source=data_source_id,
                        defaults={'name': str(subtitle_group['name'])}
                    )
                    if not if_created:
                        if s.name != str(subtitle_group['name']):
                            s.name = str(subtitle_group['name'])
                            s.save()

    @classmethod
    def get_subtitle_by_name(cls, subtitle_name_list: List[str]) -> 'List[Subtitle]':
        return cls.select().where(cls.name.in_(subtitle_name_list))

    @classmethod
    def get_subtitle_by_id(cls, subtitle_id_list: List[str]) -> 'pw.ModelSelect':
        return cls.select().where(cls.id.in_(subtitle_id_list))


class BangumiLink(NeoDB):
    value = BangumiNamesField()
    status = pw.IntegerField()

    class STATUS:
        link = 1
        unlink = 0

    @classmethod
    def get_all(cls):
        """
        :rtype: Dict[int, List[set]]
        :return:
        """
        try:
            link = []
            unlink = []

            for b in cls.select():
                if b.status == cls.STATUS.link:
                    link.append(b.value)
                if b.status == cls.STATUS.unlink:
                    unlink.append(b.value)
            return {
                cls.STATUS.link: link,
                cls.STATUS.unlink: unlink,
            }

        except BaseException:
            return {cls.STATUS.link: [], cls.STATUS.unlink: []}

    @classmethod
    def get_linked_bangumi_list(cls):
        try:
            return list(map(lambda x: x.value, cls.select().where(cls.status == cls.STATUS.link)))
        except BaseException:
            return []

    @classmethod
    def get_unlinked_bangumi_list(cls):
        try:
            return list(map(lambda x: x.value, cls.select().where(cls.status == cls.STATUS.unlink)))
        except BaseException:
            return []

    @classmethod
    def try_remove_record(cls, bangumi_name_1, bangumi_name_2, status):
        f = cls.select().where(
            cls.value.contains(bangumi_name_1) & cls.value.contains(bangumi_name_2)
            & (cls.status == status)
        )
        for v in f:
            s = v.value
            if s == {bangumi_name_2, bangumi_name_1}:
                v.delete_instance()

    @classmethod
    def add_record(cls, bangumi_name_1, bangumi_name_2, status):
        f = cls.select().where(
            cls.value.contains(bangumi_name_1) & cls.value.contains(bangumi_name_2)
            & (cls.status == status)
        )
        f = list(f)
        find = False
        for v in f:
            s = v.value
            if s == {bangumi_name_2, bangumi_name_1}:
                find = True
        if not find:
            cls.create(value={bangumi_name_1, bangumi_name_2}, status=status)

    @classmethod
    def link(cls, bangumi_name_1, bangumi_name_2):
        cls.try_remove_record(bangumi_name_1, bangumi_name_2, cls.STATUS.unlink)
        cls.add_record(bangumi_name_1, bangumi_name_2, cls.STATUS.link)

    @classmethod
    def unlink(cls, bangumi_name_1, bangumi_name_2):
        cls.try_remove_record(bangumi_name_1, bangumi_name_2, cls.STATUS.link)
        cls.add_record(bangumi_name_1, bangumi_name_2, cls.STATUS.unlink)

    def __repr__(self):
        return '<BangumiLink: {} {} {}>'.format(self.id, self.value, self.status)


class Scripts(NeoDB):
    bangumi_name = pw.CharField(null=False, unique=True)
    episode = pw.IntegerField(default=0)
    status = pw.IntegerField(default=0)
    updated_time = pw.IntegerField(default=0)
