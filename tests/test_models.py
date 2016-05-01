# coding=utf-8
from __future__ import print_function, unicode_literals
import os
import unittest
import sqlite3
from bgmi.models import Bangumi, Followed, STATUS_FOLLOWED, STATUS_NORMAL
from bgmi.sql import CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED, CREATE_TABLE_DOWNLOAD
import bgmi.config

bgmi.config.DB_PATH = '/tmp/bangumi.db'
DB_PATH = bgmi.config.DB_PATH


class ModelsTest(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(DB_PATH):
            self.db = sqlite3.connect(DB_PATH)
            self.conn = self.db.cursor()
            self.conn.execute(CREATE_TABLE_BANGUMI)
            self.conn.execute(CREATE_TABLE_FOLLOWED)
            self.conn.execute(CREATE_TABLE_DOWNLOAD)
        else:
            self.db = sqlite3.connect(DB_PATH)
            self.conn = self.db.cursor()
        self.db.commit()

    def tearDown(self):
        self.db.close()
        os.remove(DB_PATH)

    def test_select_and_save(self):
        b2 = Bangumi(name='test_select_and_save', update_time='Sun')
        d = b2.select()
        self.assertEqual(d, [])
        b2.save()
        ret = b2.select(one=True)
        self.assertIsInstance(ret, dict)

    def test_get_all_bangumi(self):
        from collections import defaultdict
        self.assertIsInstance(Bangumi.get_all_bangumi(), defaultdict)

    def test_update(self):
        b1 = Bangumi(name='test_update', update_time='Sun')
        b1.save()
        b1.update_time = 'Mon'
        b1.update()
        ret = b1.select(one=True)
        self.assertEqual(ret['update_time'], 'Mon')

        b1.update(data={'name': 'test666', 'update_time': 'Sat'})
        ret = b1.select(one=True)
        self.assertIsInstance(ret, dict)

    def test_delete(self):
        b1 = Bangumi(name='test_delete', update_time='Sun')
        b1.save()
        self.assertEqual(b1.select(one=True)['name'], 'test_delete')
        b1.delete()
        self.assertEqual(b1.select(one=True), None)

    def test_delete_bangumi(self):
        # Deprecated test

        # b1 = Bangumi(name='test_delete_all', update_time='Sun')
        # b2 = Bangumi(name='test_delete_all2', update_time='Sun')
        # Bangumi.delete_bangumi()
        # self.assertEqual(b1.select(one=True), None)
        # self.assertEqual(b2.select(one=True), None)
        pass


class FollowedTest(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(DB_PATH):
            self.db = sqlite3.connect(DB_PATH)
            self.conn = self.db.cursor()
            self.conn.execute(CREATE_TABLE_BANGUMI)
            self.conn.execute(CREATE_TABLE_FOLLOWED)
            self.conn.execute(CREATE_TABLE_DOWNLOAD)
        else:
            self.db = sqlite3.connect(DB_PATH)
            self.conn = self.db.cursor()
        self.db.commit()

    def tearDown(self):
        self.db.close()
        os.remove(DB_PATH)

    def test_add_and_remove_followed(self):
        f = Followed(bangumi_name='test_add_and_remove_followed', status=STATUS_FOLLOWED, episode=6)
        f.save()
        b = Bangumi(name='test_add_and_remove_followed')
        b.save()
        bangumi_data = b.select(one=True, join='LEFT JOIN %s ON %s.bangumi_name=%s.name' % (Followed.table,
                                                                                            Followed.table,
                                                                                            Bangumi.table))
        self.assertEqual(bangumi_data['status'], STATUS_FOLLOWED)
        f.delete()
        bangumi_data = b.select(one=True, join='LEFT JOIN %s ON %s.bangumi_name=%s.name' % (Followed.table,
                                                                                            Followed.table,
                                                                                            Bangumi.table))
        self.assertEqual(bangumi_data['status'], STATUS_NORMAL)
