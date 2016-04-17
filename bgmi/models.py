# coding=utf-8
import os
import sqlite3
from collections import defaultdict


STATUS_NORMAL = 0
STATUS_FOLLOWED = 1
STATUS_REMOVED = 2

DB_PATH = os.path.join(os.path.dirname(__file__), '../bangumi.db')


class DB(object):
    _id = None
    fields = ()
    table = None
    conn = None

    def __init__(self, **kwargs):
        for f in self.fields:
            setattr(self, f, kwargs.get(f, ''))

    @staticmethod
    def _make_sql(method, table, fields=None, data=None, condition=None, join=None):
        if method not in ('select', 'update', 'delete', 'insert'):
            raise Exception('unexpected operation %s' % method)

        if not isinstance(condition, (type(None), tuple, list, set, str)):
            raise Exception('`condition` expected sequences')

        if not isinstance(fields, (type(None), tuple, list, set, str)):
            raise Exception('`select` expected sequences or string')

        if not isinstance(table, str):
            raise Exception('unexpected type %s of table' % type(table))

        def make_condition(condition, operation='AND'):
            if not condition:
                return '1'

            sql = ''

            if isinstance(condition, (tuple, list, set)):
                for f in condition:
                    if '.' in f:
                        sql += '%s=? %s ' % (f, operation)
                    else:
                        sql += '`%s`=? %s ' % (f, operation)
                sql = sql[:-(len(operation)+1)]
            elif isinstance(condition, str):
                if '.' in condition:
                    sql += '%s=?' % condition
                else:
                    sql += '`%s`=?' % condition
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
                if not isinstance(fields, str):
                    select = ''
                    for f in fields:
                        if '.' in f:
                            select += '%s,' % f
                        else:
                            select += '`%s`,' % f
                    select = select[:-1]
                else:
                    select = '`%s`' % fields

            if not isinstance(join, str):
                join = ''

            sql = 'SELECT %s FROM `%s` %s WHERE ' % (select, table, join)
            sql += make_condition(condition)

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
                v = unicode(v.decode('utf-8'))
                self.__dict__[i] = v

    @staticmethod
    def connect_db():
        return sqlite3.connect(DB_PATH)

    @staticmethod
    def close_db(db_instance):
        db_instance.commit()
        db_instance.close()

    def _connect_db(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _close_db(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def _pair(self):
        values = tuple([self.__dict__.get(i, '') for i in self.fields])
        return self.fields, values

    def select(self, fields=None, condition=None, one=False):
        if not isinstance(condition, (dict, type(None))):
            raise Exception('condition expected dict')
        if condition is None:
            if self._id is None:
                k = []
                v = []
                for i in self.fields:
                    if self.__dict__.get(i, None):
                        k.append(i)
                        v.append(self.__dict__.get(i))
            else:
                k, v = ('id', ), (self._id, )
        else:
            k, v = condition.keys(), condition.values()

        self._connect_db()
        sql = Bangumi._make_sql('select', fields=fields, table=self.table, condition=k)
        self.cursor.execute(sql, v)
        ret = self.cursor.fetchall() if not one else self.cursor.fetchone()
        self._close_db()

        if ret and one:
            self._id = ret['id']

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
                data.update({i: self.__dict__.get(i, '')})

        sql = self._make_sql('update', self.table, fields=data.keys(), condition=('id', ))
        self._connect_db()
        params = data.values()
        params.append(self._id)
        self.cursor.execute(sql, params)
        self._close_db()

    def delete(self, condition=None):
        if not self._id:
            obj = self.select(one=True)
            if not obj:
                raise Exception('%s not exist' % self.__repr__())

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


class Bangumi(DB):
    table = 'bangumi'
    fields = ('name', 'update_time', 'subtitle_group', 'keyword')
    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def __init__(self, **kwargs):
        super(Bangumi, self).__init__(**kwargs)

        if 'name' not in kwargs:
            raise ValueError('bangumi name required')
        update_time = kwargs.get('update_time', '').title()
        if update_time and update_time not in self.week:
            raise ValueError('unexcept update time %s' % update_time)
        self.update_time = update_time
        self.subtitle_group = ', '.join(kwargs.get('subtitle_group', []))
        self._unicodeize()

    def __repr__(self):
        return self.name

    def __str__(self):
        return 'Bangumi<%s>' % self.name

    @staticmethod
    def get_all_bangumi(status=None):
        db = Bangumi.connect_db()
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        join_sql = Bangumi._make_sql('select', table=Followed.table)
        if status is None:
            sql = Bangumi._make_sql('select', fields=['%s.*' % Bangumi.table, 'status', 'episode'], table=Bangumi.table,
                                    join='LEFT JOIN (%s) AS F ON bangumi.name=F.bangumi_name' % join_sql)
            cur.execute(sql)
        else:
            sql = Bangumi._make_sql('select', fields=['%s.*' % Bangumi.table, 'status', 'episode'], table=Bangumi.table,
                                    join='LEFT JOIN (%s) AS F ON bangumi.name=F.bangumi_name' % join_sql,
                                    condition='F.status')
            cur.execute(sql, (status, ))
        data = cur.fetchall()
        Bangumi.close_db(db)

        weekly_list = defaultdict(list)

        for bangumi_item in data:
            weekly_list[bangumi_item['update_time'].lower()].append(dict(bangumi_item))

        return weekly_list

    @staticmethod
    def delete_bangumi(condition=None, batch=True):
        db = Bangumi.connect_db()
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        if not isinstance(condition, (type(None), dict)):
            raise Exception('condition expected dict')
        if condition is None:
            k, v = [], []
        else:
            k, v = condition.keys(), condition.values()
        sql = Bangumi._make_sql('delete', table=Bangumi.table, condition=k)

        if not batch and sql.endswith('WHERE 1'):
            if raw_input('are you sure clear ALL THE BANGUMI? (Y/n): ') == 'n':
                return

        cur.execute(sql, v)
        Bangumi.close_db(db)


class Followed(DB):
    table = 'followed'
    fields = ('bangumi_name', 'episode', 'status')
