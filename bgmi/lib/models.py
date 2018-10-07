# coding=utf-8
from __future__ import print_function, unicode_literals

import time
import os
from collections import defaultdict
# from typing import List

import peewee
from peewee import IntegerField, FixedCharField, TextField
from playhouse.shortcuts import model_to_dict

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

if os.environ.get('DEV'):
    print('using', bgmi.config.DB_PATH)


class NeoDB(peewee.Model):
    class Meta:
        database = db


class Bangumi(NeoDB):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True, null=False)
    subtitle_group = TextField(null=False)
    keyword = TextField()
    update_time = FixedCharField(5, null=False)
    cover = TextField()
    status = IntegerField(default=0)

    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, **kwargs):
        super(NeoDB, self).__init__(**kwargs)

        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in self.week:
            raise ValueError('unexpected update time %s' % update_time)
        self.update_time = update_time
        if isinstance(kwargs.get('subtitle_group'), list):
            self.subtitle_group = ', '.join(kwargs.get('subtitle_group', []))

    @classmethod
    def delete_all(cls):
        un_updated_bangumi = Followed.select().where(
            Followed.updated_time > (int(time.time()) - 2 * 7 * 24 * 3600))  # type: list[Followed]
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
    def fuzzy_get(cls, **filters):
        q = []
        for key, value in filters.items():
            q.append(getattr(cls, key).contains(value))
        o = list(cls.select().where(*q))
        if not o:
            raise cls.DoesNotExist
        else:
            return o[0]


class Followed(NeoDB):
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)

    class Meta:
        database = db
        table_name = 'followed'

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
    subtitle = TextField()
    include = TextField()
    exclude = TextField()
    regex = TextField()


class Subtitle(NeoDB):
    id = TextField(primary_key=True, unique=True)
    name = TextField()

    @classmethod
    def get_subtitle_by_id(cls, id_list=None):
        data = list(cls.select().where(cls.id.in_(id_list)))
        for index, subtitle in enumerate(data):
            data[index] = model_to_dict(subtitle)
        return data

    @classmethod
    def get_subtitle_by_name(cls, name_list=None):
        data = list(cls.select().where(cls.name.in_(name_list)))
        for index, subtitle in enumerate(data):
            data[index] = model_to_dict(subtitle)
        return data


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
