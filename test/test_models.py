# coding=utf-8
import os
import unittest
import sqlite3
from bgmi.models import Bangumi, STATUS_FOLLOWED
from bgmi.sql import CREATE_TABLE_BANGUMI, CREATE_TABLE_FOLLOWED, INSERT_TEST_DATA


class ModelsTest(unittest.TestCase):
    def setUp(self):
        db_path = os.path.join(os.path.dirname(__file__), '../bangumi.db')
        if not os.path.exists(db_path):
            self.db = sqlite3.connect(db_path)
            self.conn = self.db.cursor()
            self.conn.execute(CREATE_TABLE_BANGUMI)
            self.conn.execute(CREATE_TABLE_FOLLOWED)
        else:
            self.db = sqlite3.connect(db_path)
            self.conn = self.db.cursor()
            self.conn.execute(INSERT_TEST_DATA)
        self.db.commit()

    def tearDown(self):
        self.conn.execute('DELETE FROM bangumi WHERE name="test"')
        self.conn.execute('DELETE FROM bangumi WHERE name="test2"')
        self.conn.execute('DELETE FROM bangumi WHERE name="test666"')
        self.conn.execute('DELETE FROM bangumi WHERE name="test_update"')
        self.db.commit()
        self.db.close()

    def test_select_and_save(self):
        b1 = Bangumi(name='test', update_time='Sun')
        test = b1.select(condition={'name': 'test', 'status': 0}, one=True)
        self.assertEqual(list(test)[1:], [u'test', u'rr', u'test', u'Sun', u'0'])
        b2 = Bangumi(name='test2', update_time='Sun')
        d = b2.select()
        self.assertEqual(d, [])
        b2.save()
        ret = b2.select(one=True)
        self.assertEqual(list(ret)[1:], [u'test2', u'', u'', u'Sun', u'0'])

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
        b1.update(data={'name': 'test666', 'status': STATUS_FOLLOWED})
        ret = b1.select(one=True)
        self.assertEqual(list(ret)[1:], [u'test666', u'', u'', u'Mon', u'%d' % STATUS_FOLLOWED])

    def test_delete(self):
        b1 = Bangumi(name='test_delete', update_time='Sun')
        b1.save()
        self.assertEqual(b1.select(one=True)['name'], 'test_delete')
        b1.delete()
        self.assertEqual(b1.select(one=True), None)

    def test_delete_bangumi(self):
        b1 = Bangumi(name='test_delete_all', update_time='Sun')
        b2 = Bangumi(name='test_delete_all2', update_time='Sun')
        Bangumi.delete_bangumi()
        self.assertEqual(b1.select(one=True), None)
        self.assertEqual(b2.select(one=True), None)
