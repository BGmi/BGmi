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

from bgmi import config
from bgmi.lib.constants import SECOND_OF_WEEK

from ._db import FuzzyMixIn, NeoDB, db

BANGUMI_NAME_MAX_LENGTH = 255
DATA_SOURCE_ID_MAX_LENGTH = 30


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
    name = pw.CharField(max_length=BANGUMI_NAME_MAX_LENGTH)  # type: str
    cover = pw.CharField()  # type: str
    status = pw.IntegerField()  # type: int
    update_time = pw.FixedCharField(5, null=False)  # type: str
    subtitle_group = pw.TextField()  # type: str
    keyword = pw.CharField()  # type: str
    data_source = pw.FixedCharField(max_length=DATA_SOURCE_ID_MAX_LENGTH)  # type: str
    # foreign key
    bangumi = pw.IntegerField(default=0)

    class STATUS(IntEnum):
        UPDATING = 0
        END = 1

    def __getitem__(self, item):
        return getattr(self, item)

    def __init__(self, *args, **kwargs):
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
    def get_data_source_by_id(cls, bangumi_id) -> Iterator['BangumiItem']:
        return cls.select().where(cls.bangumi == bangumi_id)


class Bangumi(FuzzyMixIn, NeoDB):
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
            print(
                'ignore updating bangumi',
                [cls.get(id=x.bangumi_id).name for x in un_updated_bangumi]
            )

        cls.update(status=cls.STATUS.END) \
            .where(cls.id.not_in([x.bangumi_id for x in un_updated_bangumi])) \
            .execute()  # do not mark updating bangumi as Bangumi.STATUS.END

    @classmethod
    def get_updating_bangumi(cls, status=None, order=True, obj=False) -> Dict:
        base_cond = (cls.status == cls.STATUS.UPDATING)
        query = cls.select(Followed.status, Followed.episode, cls, ) \
            .join(Followed, pw.JOIN['LEFT_OUTER'], on=(cls.id == Followed.bangumi_id))

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
    bangumi_id = pw.IntegerField(primary_key=True)
    # bangumi = pw.ForeignKeyField(Bangumi, backref='followed', unique=True)  # type: Bangumi
    # bangumi_name = pw.CharField(unique=True, primary_key=True)
    episode = pw.IntegerField(null=True, default=0)
    status = pw.IntegerField(null=True)
    updated_time = pw.IntegerField(null=True)

    # followed filter
    data_source = pw.FixedCharField(default='')  # type:str
    subtitle = pw.CharField(default='')  # type:str
    include = pw.CharField(default='')  # type:str
    exclude = pw.CharField(default='')  # type: str
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
        join_cond = (Bangumi.id == cls.bangumi_id)
        d = cls.select(
            Bangumi.name,
            Bangumi.update_time,
            Bangumi.cover,
            cls,
            cls.episode,
            Bangumi.name.alias('bangumi_name'),
        ).join(
            Bangumi,
            pw.JOIN['LEFT_OUTER'],
            on=join_cond,
        ).where((cls.status != status) & (Bangumi.status == bangumi_status)).order_by(
            cls.updated_time.desc()
        ).dicts()

        return list(d)

    def apply_keywords_filter_on_list_of_episode(self, episode_list: List[Dict]) -> List[Dict]:
        episode_list = self.apply_include(episode_list)
        episode_list = self.apply_exclude(episode_list)
        episode_list = self.apply_regex(episode_list)
        return episode_list

    def apply_include(self, episode_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.include:

            def f1(s):
                return all(map(lambda t: t in s['title'], split_str_to_list(self.include)))

            episode_list = list(filter(f1, episode_list))
        return episode_list

    def apply_exclude(self, episode_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.exclude:
            exclude = split_str_to_list(self.exclude)
        else:
            exclude = []
        if config.ENABLE_GLOBAL_FILTER != '0':
            exclude += split_str_to_list(config.GLOBAL_FILTER)
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

    @classmethod
    def get_by_name(cls, bangumi_name):
        if config.SHOW_WARNING:
            import warnings
            warnings.warn('should use Followed.get(id=bangumi_obj.id) instead of get by name')
        return cls.get(bangumi_id=Bangumi.get(name=bangumi_name).id)


def split_str_to_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(',')]


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
    data_source = pw.CharField(max_length=DATA_SOURCE_ID_MAX_LENGTH)

    # data_source = pw.CharField(max_length=255)

    class Meta:
        database = db
        indexes = (
            # create a unique on from/to/date
            (('id', 'data_source'), True),
        )

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
            condition.append((Subtitle.id.in_(split_str_to_list(data_source[s]['subtitle_group'])))
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


class Scripts(NeoDB):
    bangumi_name = pw.CharField(max_length=BANGUMI_NAME_MAX_LENGTH, unique=True)
    episode = pw.IntegerField(default=0)
    status = pw.IntegerField(default=0)
    updated_time = pw.IntegerField(default=0)
