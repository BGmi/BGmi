# coding=utf-8
from __future__ import print_function, unicode_literals

from collections import defaultdict

import peewee
from peewee import *

import bgmi.config
from bgmi.config import IS_PYTHON3

if IS_PYTHON3:
    _unicode = str
else:
    input = raw_input
    _unicode = unicode

# bangumi status
STATUS_UPDATING = 0
STATUS_END = 1
BANGUMI_STATUS = (STATUS_UPDATING, STATUS_END)

# subscription status
STATUS_NORMAL = 0
STATUS_FOLLOWED = 1
STATUS_UPDATED = 2
FOLLOWED_STATUS = (STATUS_NORMAL, STATUS_FOLLOWED, STATUS_UPDATED)

# download status
STATUS_NOT_DOWNLOAD = 0
STATUS_DOWNLOADING = 1
STATUS_DOWNLOADED = 2
DOWNLOAD_STATUS = (STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING, STATUS_DOWNLOADED)

db = peewee.SqliteDatabase(bgmi.config.DB_PATH)

compiler = db.compiler()
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))




class NeoDB(Model):
    class Meta:
        database = db


class Bangumi(NeoDB):
    class Meta:
        database = db
        db_table = 'bangumi'

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
            raise ValueError('unexcept update time %s' % update_time)
        self.update_time = update_time
        self.subtitle_group = ', '.join(kwargs.get('subtitle_group', []))


    @classmethod
    def delete_all(cls):
        cls.update(status=STATUS_END).execute()

    @classmethod
    def get_all_bangumi(cls, status=None, order=True):
        from playhouse.shortcuts import model_to_dict

        if status is None:
            data = cls.select(cls) \
                .join(Followed, JOIN_LEFT_OUTER, on=(cls.name == Followed.bangumi_name)) \
                .where(cls.status == STATUS_UPDATING).naive()
        else:
            data = cls.select(cls) \
                .join(Followed, JOIN_LEFT_OUTER, on=(cls.name == Followed.bangumi_name)) \
                .where(cls.status == STATUS_UPDATING and Followed.status == status)

        data = [model_to_dict(x) for x in data]

        if order:
            weekly_list = defaultdict(list)
            for bangumi_item in data:
                weekly_list[bangumi_item['update_time'].lower()].append(dict(bangumi_item))
        else:
            weekly_list = data

        return weekly_list


class Followed(NeoDB):
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)


    class Meta:
        database = db
        db_table = 'followed'

    @classmethod
    def delete_followed(cls, batch=True):
        q = cls.delete()
        if not batch:
            if not input('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ') == 'y':
                return False

        q.execute()
        return True

    @classmethod
    def get_all_followed(cls, status=STATUS_NORMAL, bangumi_status=STATUS_UPDATING, order=None, desc=None):
        join_cond = (Bangumi.name == cls.bangumi_name)
        if status is None and bangumi_status is None:
            d = cls.select(cls, Bangumi.name, Bangumi.update_time) \
                .join(Bangumi.name, JOIN_LEFT_OUTER, on=join_cond) \
                .naive()
            # print(d.sql())
        else:
            d = cls.select(cls, Bangumi.name, Bangumi.update_time) \
                .join(Bangumi, JOIN_LEFT_OUTER, on=join_cond) \
                .where(cls.status != status or Bangumi.status == bangumi_status) \
                .naive()

        r = []
        for x in d:
            dic = dict(**x.__dict__['_data'])
            dic['update_time'] = x.update_time
            r.append(dic)
        return r

    def __str__(self):
        return 'Followed Bangumi<%s>' % self.bangumi_name

    def __repr__(self):
        return 'Followed Bangumi<%s>' % self.bangumi_name


class Download(NeoDB):
    name = TextField(null=False)
    title = TextField(null=False)
    episode = IntegerField(default=0)
    download = TextField()
    status = IntegerField(default=0)

    # add_time
    # end_time
    class Meta:
        database = db
        db_table = 'download'

    @classmethod
    def get_all_downloads(cls, status=None):
        if status is None:
            data = list(cls.select().order_by(cls.status))
        else:
            data = list(cls.select().where(cls.status == status).order_by(cls.status))

        for index, x in enumerate(data):
            data[index] = x.__dict__['_data']
        return data

    def downloaded(self, condition=None):
        self.status = STATUS_DOWNLOADED
        self.save()


script_db = peewee.SqliteDatabase(bgmi.config.SCRIPT_DB_PATH)


class Scripts(peewee.Model):
    bangumi_name = TextField(null=False, unique=True)
    episode = IntegerField(default=0)
    status = IntegerField(default=0)
    updated_time = IntegerField(default=0)

    class Meta:
        database = script_db


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
            data[index] = subtitle.__dict__['_data']
        return data

    @classmethod
    def get_subtitle_by_name(cls, name_list=None):
        data = list(cls.select().where(cls.name.in_(name_list)))
        for index, subtitle in enumerate(data):
            data[index] = subtitle.__dict__['_data']
        return data


def recreate_source_relatively_table():
    table_to_drop = [Bangumi, Followed, Subtitle, Filter, Download]
    for table in table_to_drop:
        q = table.delete().execute()
    return True


def init_db():
    """
    初始化数据库
    :return:
    """

    db.create_tables([Followed, Bangumi, Download, Filter, Subtitle])
    script_db.connect()
    script_db.create_tables([Scripts, ])
    script_db.close()


if __name__ == '__main__':
    x = recreate_source_relatively_table()
    print(x)
