# coding=utf-8
from __future__ import print_function, unicode_literals
import sys
import sqlite3
from collections import defaultdict
import bgmi.config
from bgmi.config import IS_PYTHON3

if IS_PYTHON3:
    _unicode = str
else:
    input = raw_input
    _unicode = unicode


# bangumi subscription and download status
STATUS_UPDATING = 0
STATUS_END = 1
BANGUMI_STATUS = (STATUS_UPDATING, STATUS_END)

STATUS_NORMAL = 0
STATUS_FOLLOWED = 1
STATUS_UPDATED = 2
FOLLOWED_STATUS = (STATUS_NORMAL, STATUS_FOLLOWED, STATUS_UPDATED)

STATUS_NOT_DOWNLOAD = 0
STATUS_DOWNLOADING = 1
STATUS_DOWNLOADED = 2
DOWNLOAD_STATUS = (STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING, STATUS_DOWNLOADED)


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


class FalseType(type):
    def __nonzero__(self):
        return False


class DB(object):
    # `_id` save the id column in database, will be set automatic
    _id = None

    # `primary_key` is one of the fields in a table, which maybe `UNIQUE` or `PRIMARY_KEY`.
    # It will be set when instantiate a DB object, and `primary_key` is used as query condition
    # when `_id` is `None`.
    primary_key = None

    # all columns of a table except `id`, must be a sequence instance.
    fields = ()

    # table name
    table = None
    _conn = None

    # nonzero
    __nonzero = True

    def __init__(self, **kwargs):
        if '_id' in kwargs:
            self._id = kwargs.get('_id')

        for f in self.fields:
            if f in self.primary_key and kwargs.get(f, None) is None:
                if '_id' not in kwargs:
                    raise ValueError('primary key %s must be set' % f)
            setattr(self, f, kwargs.get(f, None))

        self._unicodeize()
        self.select(one=True)

    def __getitem__(self, item):
        return getattr(self, item)

    @staticmethod
    def _make_sql(method, table, fields=None, data=None, condition=None, join=None, order=None, desc=None):
        '''
        Make SQL statement (just a simple implementation, don't support complex operation).

        :param method: expect `select`, `update`, `delete`, `insert`
        :param table: the main table name of the SQL statement
        :param fields: fields will be operated
        :param data:
        :param condition: conditions, only support sequences
        :param join:
        :return:
        '''
        if method not in ('select', 'update', 'delete', 'insert'):
            raise Exception('unexpected operation %s' % method)

        if not isinstance(condition, (type(None), tuple, list, set, _unicode)):
            raise Exception('`condition` expected sequences')

        if not isinstance(fields, (type(None), tuple, list, set, _unicode)):
            raise Exception('`select` expected sequences or string')

        if not isinstance(table, _unicode):
            raise Exception('unexpected type %s of table' % type(table))

        def make_condition(condition, operation='AND'):
            if not condition:
                return '1'

            sql = ''

            if isinstance(condition, _unicode):
                condition = (condition, )

            if isinstance(condition, (tuple, list, set)):
                for f in condition:
                    if f.startswith('!'):
                        operator = '!'
                        f = f[1:]
                    else:
                        operator = ''

                    if '.' in f:
                        name = '%s' % f
                    else:
                        name = '`%s`' % f
                    sql += '%s%s=? %s ' % (name, operator, operation)

                sql = sql[:-(len(operation)+1)]
            else:
                sql += '1'
            return sql

        def make_fields(fields):
            sql = ''
            for f in fields:
                if '.' in f:
                    sql += '%s,' % f
                else:
                    sql += '`%s`,' % f
            sql = sql[:-1]
            return sql

        if method == 'insert':
            sql = 'INSERT INTO %s ' % table
            if fields is not None:
                sql += '(%s)' % make_fields(fields)

            sql += ' VALUES ('
            for i in range(len(fields)):
                sql += '?,'
            sql = sql[:-1]
            sql += ')'

        elif method == 'select':

            if fields is None:
                select = '*'
            else:
                if not isinstance(fields, _unicode):
                    select = ''
                    for f in fields:
                        if '.' in f:
                            select += '%s,' % f
                        else:
                            select += '`%s`,' % f
                    select = select[:-1]
                else:
                    select = '`%s`' % fields

            if not isinstance(join, _unicode):
                join = ''

            sql = 'SELECT %s FROM `%s` %s WHERE ' % (select, table, join)
            sql += make_condition(condition)
            if order:
                if '.' in order:
                    sql += 'ORDER BY %s ' % order
                else:
                    sql += 'ORDER BY `%s` ' % order
            if desc:
                sql += 'DESC'

        elif method == 'update':
            sql = 'UPDATE %s SET ' % table
            if fields is not None:
                sql += make_condition(fields, ',')
            else:
                raise Exception('UPDATE: unexpected null fields')

            sql += ' WHERE '
            sql += make_condition(condition)
        elif method == 'delete':
            sql = 'DELETE FROM %s WHERE ' % table
            if condition is not None:
                sql += make_condition(condition)
            else:
                sql += '1'

        return sql

    def _unicodeize(self):
        for i in self.fields:
            v = self.__dict__.get(i, '')
            if isinstance(v, str):
                if sys.version_info.major < 3:
                    v = unicode(v.decode('utf-8'))
                else:
                    v = str(v)
                self.__dict__[i] = v

    @staticmethod
    def connect_db():
        return sqlite3.connect(bgmi.config.DB_PATH)

    @staticmethod
    def close_db(db_instance):
        db_instance.commit()
        db_instance.close()

    def _connect_db(self):
        self._conn = sqlite3.connect(bgmi.config.DB_PATH)
        self._conn.row_factory = make_dicts
        self.cursor = self._conn.cursor()

    def _close_db(self):
        self._conn.commit()
        self.cursor.close()
        self._conn.close()

    def _pair(self):
        values = tuple([self.__dict__.get(i, '') for i in self.fields])
        return self.fields, values

    def select_obj(self):
        data = self.select(one=True)
        if not data:
            self.__nonzero = False
        else:
            self.__nonzero = True
            for k, v in data.items():
                setattr(self, k, v)

    def __bool__(self):
        return self.__nonzero

    def __nonzero__(self):
        return self.__nonzero

    def select(self, fields=None, condition=None, one=False, join=None):
        if not isinstance(condition, (dict, type(None))):
            raise Exception('condition expected dict')

        if condition is None:
            if self._id is None:
                if self.primary_key:
                    k, v = self.primary_key, [self.__dict__.get(i, '') for i in self.primary_key]
                else:
                    k = []
                    v = []
                    for i in self.fields:
                        if self.__dict__.get(i, None):
                            k.append(i)
                            v.append(self.__dict__.get(i))
            else:
                k, v = '%s.id' % self.table, (self._id, )
        else:
            # hack for python3
            k, v = list(condition.keys()), list(condition.values())

        self._connect_db()
        sql = Bangumi._make_sql('select', fields=fields, table=self.table, condition=k, join=join)
        self.cursor.execute(sql, v)
        ret = self.cursor.fetchall() if not one else self.cursor.fetchone()
        self._close_db()

        if self._id is None and ret and one and 'id' in ret:
            self._id = ret['id']

        if not isinstance(ret, (list, type(None))):
            for i in self.fields:
                if getattr(self, i) is None:
                    if i in ret:
                        setattr(self, i, ret[i])

        return ret

    def update(self, data=None):
        obj = self.select(one=True)
        if obj:
            self._id = obj['id']
        else:
            raise Exception('%s not exist' % self.__repr__())

        if not isinstance(data, (dict, type(None))):
            raise Exception('update data expected dict')

        if data is None:
            data = {}
            for i in self.fields:
                data.update({i: getattr(self, i)})

        sql = self._make_sql('update', self.table, fields=list(data.keys()), condition=('id', ))
        self._connect_db()
        params = list(data.values())
        params.append(self._id)
        self.cursor.execute(sql, params)
        self._close_db()

    def delete(self, condition=None):
        if not self._id:
            obj = self.select(one=True)
            if not obj:
                raise Exception('%s does not exist' % self.__repr__())

        sql = self._make_sql('delete', self.table, condition=('id', ))
        self._connect_db()
        self.cursor.execute(sql, (self._id, ))
        self._close_db()

    def save(self):
        _f, _v = self._pair()

        obj = self.select(one=True)
        if obj:
            self._id = obj['id']
            self.update()
            return self

        self._connect_db()
        sql = self._make_sql('insert', self.table, _f)
        self.cursor.execute(sql, _v)
        self._id = self.cursor.lastrowid
        self._close_db()

        return self

    @staticmethod
    def execute(sql):
        db = DB.connect_db()
        db.execute(sql)
        DB.close_db(db)


class Bangumi(DB):
    table = 'bangumi'
    primary_key = ('name', )
    fields = ('name', 'update_time', 'subtitle_group', 'keyword', 'status', )
    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, **kwargs):
        super(Bangumi, self).__init__(**kwargs)

        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in self.week:
            raise ValueError('unexcept update time %s' % update_time)
        self.update_time = update_time
        self.subtitle_group = ', '.join(kwargs.get('subtitle_group', []))
        self._unicodeize()
        self.select(one=True)

    def __repr__(self):
        return 'Bangumi<%s>' % self.name

    def __str__(self):
        return 'Bangumi<%s>' % self.name

    @staticmethod
    def delete_all():
        db = Bangumi.connect_db()
        sql = Bangumi._make_sql('update', table=Bangumi.table, fields=('status'))
        cur = db.cursor()
        cur.execute(sql, (STATUS_END, ))
        Bangumi.close_db(db)

    @staticmethod
    def get_all_bangumi(status=None, order=True):
        db = Bangumi.connect_db()
        db.row_factory = make_dicts
        cur = db.cursor()
        join_sql = Bangumi._make_sql('select', table=Followed.table)
        if status is None:
            sql = Bangumi._make_sql('select', fields=['%s.*' % Bangumi.table, 'F.status',
                                                      'episode'], table=Bangumi.table,
                                    condition=('%s.status' % Bangumi.table),
                                    join='LEFT JOIN (%s) AS F ON bangumi.name=F.bangumi_name' % join_sql)
            cur.execute(sql, (STATUS_UPDATING, ))
        else:
            sql = Bangumi._make_sql('select', fields=['%s.*' % Bangumi.table, 'F.status',
                                                      'episode'], table=Bangumi.table,
                                    join='LEFT JOIN (%s) AS F ON bangumi.name=F.bangumi_name' % join_sql,
                                    condition=('F.status', '%s.status' % Bangumi.table))
            cur.execute(sql, (status, STATUS_UPDATING, ))
        data = cur.fetchall()
        Bangumi.close_db(db)

        if order:
            weekly_list = defaultdict(list)
            for bangumi_item in data:
                weekly_list[bangumi_item['update_time'].lower()].append(dict(bangumi_item))
        else:
            weekly_list = data

        return weekly_list


class Followed(DB):
    table = 'followed'
    primary_key = ('bangumi_name', )
    fields = ('bangumi_name', 'episode', 'status', 'updated_time', )

    @staticmethod
    def delete_followed(condition=None, batch=True):
        db = DB.connect_db()
        db.row_factory = make_dicts
        cur = db.cursor()
        if not isinstance(condition, (type(None), dict)):
            raise Exception('condition expected dict')
        if condition is None:
            k, v = [], []
        else:
            k, v = list(condition.keys()), list(condition.values())
        sql = DB._make_sql('delete', table=Followed.table, condition=k)

        if not batch and sql.endswith('WHERE 1'):
            if not input('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ') == 'y':
                return False

        cur.execute(sql, v)
        DB.close_db(db)
        return True

    def delete(self, condition=None):
        self.status = STATUS_NORMAL
        self.save()

    @staticmethod
    def get_all_followed(status=STATUS_NORMAL, bangumi_status=STATUS_UPDATING, order=None, desc=None):
        db = DB.connect_db()
        db.row_factory = make_dicts
        cur = db.cursor()
        if status is None and bangumi_status is None:
            sql = DB._make_sql('select', fields=['followed.*'], table=Followed.table,
                               join='LEFT JOIN bangumi on bangumi.name=followed.bangumi_name', order=order,
                               desc=desc)
            cur.execute(sql)
        else:
            sql = DB._make_sql('select', fields=['followed.*'], table=Followed.table,
                               join='LEFT JOIN bangumi on bangumi.name=followed.bangumi_name',
                               condition=['!followed.status', 'bangumi.status'], order=order, desc=desc)
            cur.execute(sql, (status, bangumi_status))
        data = cur.fetchall()
        DB.close_db(db)
        return data

    def __str__(self):
        return 'Followed Bangumi<%s>' % self.bangumi_name

    def __repr__(self):
        return 'Followed Bangumi<%s>' % self.bangumi_name


class Download(DB):
    table = 'download'
    primary_key = ('name', 'episode', )
    fields = ('name', 'title', 'episode', 'download', 'status', )

    @staticmethod
    def get_all_downloads(status=None):
        db = DB.connect_db()
        db.row_factory = make_dicts
        cur = db.cursor()

        if status is None:
            sql = DB._make_sql('select', table=Download.table)
            sql += ' order by status'
            cur.execute(sql)
        else:
            sql = DB._make_sql('select', table=Download.table, condition=['status', ])
            cur.execute(sql, (status, ))

        data = cur.fetchall()
        DB.close_db(db)
        return data

    def delete(self, condition=None):
        self.status = STATUS_DOWNLOADED
        self.save()


class Filter(DB):
    table = 'filter'
    primary_key = ('bangumi_name', )
    fields = ('bangumi_name', 'subtitle', 'include', 'exclude', )
