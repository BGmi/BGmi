# coding=utf-8

import time
import os
from collections import defaultdict

import peewee
from peewee import IntegerField, FixedCharField, TextField, CompositeKey
from playhouse.shortcuts import model_to_dict
from playhouse.sqlite_ext import JSONField
from typing import Dict, List, Union

import json

import bgmi.config

# bangumi status
STATUS_UPDATING = 0
STATUS_END = 1
BANGUMI_STATUS = (STATUS_UPDATING, STATUS_END)

# subscription status
STATUS_DELETED = 0
STATUS_FOLLOWED = 1
STATUS_UPDATED = 2
FOLLOWED_STATUS = (STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED)

# download status
STATUS_NOT_DOWNLOAD = 0
STATUS_DOWNLOADING = 1
STATUS_DOWNLOADED = 2
DOWNLOAD_STATUS = (STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING, STATUS_DOWNLOADED)

DoesNotExist = peewee.DoesNotExist

db = peewee.SqliteDatabase(bgmi.config.DB_PATH)


class SubtitleField(JSONField):
    def python_value(self, value):
        if value is None:
            return []
        else:
            return [x.strip() for x in value.split(',')]

    def db_value(self, value):
        if value is None:
            return ''
        else:
            return ', '.join(value)


class BangumiNamesField(JSONField):
    def python_value(self, value):
        if value is None:
            return set()
        else:
            return set([x.strip() for x in value.split(',')])

    def db_value(self, value):
        if value is not None:
            if isinstance(value, str):
                return value
            return ', '.join(value)


class DataSourceField(JSONField):

    def python_value(self, value):
        e = super().python_value(value)
        return {k: BangumiItem(**v) for k, v in e.items()}

    def db_value(self, value):
        if value is not None:
            # if isinstance(value, str):
            #     return value
            data_source = {k: model_to_dict(v) for k, v in value.items()}
            return json.dumps(data_source, ensure_ascii=False)
        # return super().db_value(data_source)


class NeoDB(peewee.Model):
    class Meta:
        database = db


class BangumiItem(peewee.Model):
    """
    This model is the item of Bangumi.data_source:Dict[str, BangumiItem]

    It will not be stored in database and there isn't a table named BangumiItem in database.
    """

    class Meta:
        primary_key = False

    name = TextField(unique=True, null=False, )  # type: str
    cover = TextField()  # type: str
    status = IntegerField(default=0)  # type: int
    keyword = TextField()
    update_time = FixedCharField(5, null=False)  # type: str
    subtitle_group = SubtitleField()  # type: List[str]

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


class Bangumi(NeoDB):
    id = IntegerField(primary_key=True)  # type: int
    name = TextField(unique=True, null=False)
    subject_name = TextField(unique=True)
    cover = TextField()
    status = IntegerField(default=0)  # type: int
    subject_id = IntegerField(null=True)
    update_time = FixedCharField(5, null=False)
    data_source = DataSourceField(default=lambda: {})  # type: Union[Dict[str, BangumiItem],JSONField]
    bangumi_names = BangumiNamesField()  # type: set

    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, **kwargs):
        super(NeoDB, self).__init__(**kwargs)

        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in self.week:
            raise ValueError('unexpected update time %s' % update_time)
        if not kwargs.get('view_name'):
            self.view_name = self.name
        self.update_time = update_time

    @classmethod
    def delete_all(cls):
        un_updated_bangumi = Followed.select() \
            .where(Followed.updated_time > (int(time.time()) - 2 * 7 * 24 * 3600))  # type: list[Followed]
        if os.getenv('DEBUG'):  # pragma: no cover
            print('ignore updating bangumi', [x.bangumi_name for x in un_updated_bangumi])

        cls.update(status=STATUS_END) \
            .where(cls.name.not_in(
            [x.bangumi_name for x in un_updated_bangumi])).execute()  # do not mark updating bangumi as STATUS_END

    @classmethod
    def get_updating_bangumi(cls, status=None, order=True):
        if status is None:
            data = cls.select(Followed.status, Followed.episode, cls, ) \
                .join(Followed, peewee.JOIN['LEFT_OUTER'], on=(cls.name == Followed.bangumi_name)) \
                .where(cls.status == STATUS_UPDATING).dicts()
        else:
            data = cls.select(Followed.status, Followed.episode, cls, ) \
                .join(Followed, peewee.JOIN['LEFT_OUTER'], on=(cls.name == Followed.bangumi_name)) \
                .where((cls.status == STATUS_UPDATING) & (Followed.status == status)).dicts()

        if order:
            weekly_list = defaultdict(list)
            for bangumi_item in data:
                weekly_list[bangumi_item['update_time'].lower()].append(dict(bangumi_item))
        else:
            weekly_list = list(data)

        return weekly_list

    @classmethod
    def get_all_bangumi(cls):
        return cls.select().dicts()

    def add_data_source(self, source, bangumi):
        if isinstance(bangumi, dict):
            self.data_source[source] = BangumiItem(**bangumi)
        elif isinstance(bangumi, BangumiItem):
            self.data_source[source] = bangumi
        else:
            raise ValueError('data_source item must be type dict or BangumiItem, can\'t be {} {}'.format(type(bangumi),
                                                                                                         bangumi))

    def get_subtitle_of_bangumi(self) -> 'List[Subtitle]':
        """
        :type bangumi_obj: Bangumi
        """
        return Subtitle.get_subtitle_of_bangumi(self)

    @classmethod
    def create(cls, **query):
        if not query.get('subject_name'):
            query['subject_name'] = query['name']
        return super().create(**query)

    def __str__(self):
        d = model_to_dict(self)
        d['data_source'] = {}
        d['bangumi_names'] = '{}'.format(self.bangumi_names)
        for key, value in self.data_source.items():
            d['data_source'][key] = str(value)
        return '<Bangumi {}>'.format(json.dumps(d, ensure_ascii=False))

    def __repr__(self):
        return self.__str__()


class Followed(NeoDB):
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True, default=0)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)

    class Meta:
        database = db

    @classmethod
    def delete_followed(cls, batch=True):
        q = cls.delete()
        if not batch:
            if not input('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ') == 'y':
                return False

        q.execute()
        return True

    @classmethod
    def get_all_followed(cls, status=STATUS_DELETED, bangumi_status=STATUS_UPDATING):
        join_cond = (Bangumi.name == cls.bangumi_name)
        d = cls.select(Bangumi.name, Bangumi.update_time, Bangumi.cover, cls, ) \
            .join(Bangumi, peewee.JOIN['LEFT_OUTER'], on=join_cond) \
            .where((cls.status != status) & (Bangumi.status == bangumi_status)) \
            .order_by(cls.updated_time.desc()) \
            .dicts()

        return list(d)


class Download(NeoDB):
    name = TextField(null=False)
    title = TextField(null=False)
    episode = IntegerField(default=0)
    download = TextField()
    status = IntegerField(default=0)

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
        self.status = STATUS_DOWNLOADED
        self.save()


class Filter(NeoDB):
    bangumi_name = TextField(unique=True)
    data_source = TextField(null=True)
    subtitle = TextField(null=True)
    include = TextField(null=True)
    exclude = TextField(null=True)
    regex = TextField(null=True)

    def apply_on_list_of_episode(self, episode_list: List[Dict[str, str]]):
        pass


class Subtitle(NeoDB):
    id = TextField()
    name = TextField()
    data_source = TextField()

    class Meta:
        database = db
        indexes = (
            # create a unique on from/to/date
            (('id', 'data_source'), True),
        )
        primary_key = CompositeKey('id', 'data_source')

    @classmethod
    def get_subtitle_of_bangumi(cls, bangumi_obj):
        """
        :type bangumi_obj: Bangumi
        """
        return cls.get_subtitle_from_data_source_dict(bangumi_obj.data_source)

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
            condition.append(
                (Subtitle.id.in_(data_source[s]['subtitle_group'])) & (Subtitle.data_source == s)
            )
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
        for data_source_id, subtitle_group_list in subtitle_group_list.items():
            for subtitle_group in subtitle_group_list:
                with db.atomic():
                    s, if_created = Subtitle.get_or_create(id=str(subtitle_group['id']),
                                                           data_source=data_source_id,
                                                           defaults={'name': str(subtitle_group['name'])})
                    if not if_created:
                        if s.name != str(subtitle_group['name']):
                            s.name = str(subtitle_group['name'])
                            s.save()

    @classmethod
    def get_subtitle_by_name(cls, subtitle_name_list: List[str]) -> 'List[Subtitle]':
        return cls.select().where(cls.name.in_(subtitle_name_list))

    @classmethod
    def get_subtitle_by_id(cls, subtitle_id_list: List[str]) -> 'peewee.ModelSelect':
        l = cls.select().where(cls.id.in_(subtitle_id_list))
        # cls.select().dicts()
        return l


script_db = peewee.SqliteDatabase(bgmi.config.SCRIPT_DB_PATH)


class Scripts(peewee.Model):
    bangumi_name = TextField(null=False, unique=True)
    episode = IntegerField(default=0)
    status = IntegerField(default=0)
    updated_time = IntegerField(default=0)

    class Meta:
        database = script_db


def recreate_source_relatively_table():
    table_to_drop = [Bangumi, Followed, Subtitle, Filter, Download]
    for table in table_to_drop:
        table.delete().execute()
    return True


if __name__ == '__main__':  # pragma:no cover
    from pprint import pprint

    d = Bangumi.get_updating_bangumi(status=STATUS_FOLLOWED)
    pprint(d)
