import os
import time
from unittest import TestCase
from unittest.mock import Mock, patch

import faker

from bgmi.lib import db_models
from bgmi.lib.db_models import Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle, db

DB_SQL_PATH = os.getenv('DB_SQL_PATH')
with open(DB_SQL_PATH, 'r', encoding='utf8') as f:
    SQL = f.read()


class Base:
    faker = faker.Faker()

    def setUp(self):
        db.create_tables([Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle])
        Bangumi.delete().where(True).execute()
        Followed.delete().where(True).execute()
        BangumiItem.delete().where(True).execute()
        Subtitle.delete().where(True).execute()
        for line in SQL.splitlines():
            if line:
                db.execute_sql(line.replace('%', '%%'))
        db.close()


class BangumiTest(Base, TestCase):
    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def test__init__(self, **kwargs):
        self.assertRaises(ValueError, lambda: Bangumi(update_time='wrong'))
        query = {'update_time': 'wed', 'subtitle_group_id': ['1', '2', '3']}
        b = Bangumi(**query)
        self.assertEqual(b.update_time, 'Wed')
        self.assertIn(b.update_time, b.week)
        self.assertEqual(b.subtitle_group_id, ['1', '2', '3'])

    """
    class Bangumi(NeoDB):
        id = pw.AutoField(primary_key=True)  # type: Union[int, pw.AutoField]
        name = pw.CharField(unique=True, null=False)  # type: Union[str, pw.CharField]
        # subject_name = pw.CharField(unique=True)
        cover = pw.CharField(default='')
        status = pw.IntegerField(default=0)  # type: int
        subject_id = pw.IntegerField(null=True)
        update_time = pw.FixedCharField(5, null=False)

        has_data_source = pw.IntegerField(default=0)
    """
    def test_delete_all(self):
        now = int(time.time())
        name_updating = []
        for i in range(5):
            name = self.faker.name()
            bangumi_obj = Bangumi.create(
                name=name,
                keyword=name,
                cover=name,
                update_time='mon',
                status=Bangumi.STATUS.UPDATING
            )
            Followed.create(bangumi_id=bangumi_obj.id, updated_time=now + i)
            name_updating.append(name)

        name_end = []
        for _ in range(5):
            name = self.faker.name()
            bangumi_obj = Bangumi.create(
                name=name,
                keyword=name,
                cover=name,
                update_time='mon',
                status=db_models.Bangumi.STATUS.UPDATING
            )
            Followed.create(
                bangumi_id=bangumi_obj.id, updated_time=now - 2 * 2 * 7 * 24 * 3600 - 200
            )
            name_end.append(name)

        Bangumi.delete_all()

        for bangumi in Bangumi.select().where(Bangumi.name.in_(name_updating)):
            self.assertEqual(bangumi.status, db_models.Bangumi.STATUS.UPDATING)

        for bangumi in Bangumi.select().where(Bangumi.name.in_(name_end)):
            self.assertEqual(bangumi.status, db_models.Bangumi.STATUS.END)

    def test_get_updating_bangumi(self):
        # old_bangumi = ['机动奥特曼']
        bgm_followed = ['海贼王']
        bgm_updated = ['名侦探柯南']

        b1 = Bangumi.get_updating_bangumi(status=Followed.STATUS.FOLLOWED, order=True)
        b2 = Bangumi.get_updating_bangumi(status=Followed.STATUS.UPDATED, order=True)
        b3 = Bangumi.get_updating_bangumi(order=False)

        for key, value in b1.items():
            self.assertIn(key.title(), Bangumi.week)
            for bangumi in value:
                self.assertIn(bangumi['name'], bgm_followed)

        for key, value in b2.items():
            self.assertIn(key.title(), Bangumi.week)
            self.assertFalse([])
            for v in value:  #
                self.assertIn(v['name'], bgm_updated)

        updating_bangumi_names = [
            x.name
            for x in Bangumi.select(Bangumi.name).where(Bangumi.status == Bangumi.STATUS.UPDATING)
        ]
        for bangumi in b3:
            self.assertIn(bangumi['name'], updating_bangumi_names)

    def test_get_all_bangumi(self):
        Bangumi.delete().execute()

        Bangumi.create(name='name', cover='name', update_time='mon', status=Bangumi.STATUS.UPDATING)
        b = Bangumi.get_all_bangumi()
        for bg in b:
            self.assertEqual(bg['name'], 'name')
            self.assertEqual(bg['cover'], 'name')


class FollowedTest(Base, TestCase):
    def test_delete_followed(self):
        Followed.create(bangumi_id=233)
        with patch('builtins.input', Mock(return_value='n')) as m:
            Followed.delete_followed(batch=False)
            m.assert_any_call('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ')
            m.return_value = 'y'
            Followed.delete_followed(batch=False)
        self.assertFalse(Followed.select())

    def test_get_all_followed(self):
        Followed.get_all_followed()


class SubtitleTest(Base, TestCase):
    def test_get_subtitle_of_bangumi(self):
        """
        todo: need to fix this
        :type bangumi_obj: Bangumi
        """
        r = [{'123': '456'}]

        class B(Bangumi):
            data_source = {'dmhy': {}}

        with patch(
            'bgmi.lib.db_models.Subtitle.get_subtitle_from_data_source_dict', Mock(return_value=r)
        ) as m:
            Subtitle.get_subtitle_of_bangumi(B())
            m.assert_called_with({})

    def test_get_subtitle_from_data_source_dict(self):
        """
        :type data_source_id: dict
        :param data_source_id:
        :return:
        """
        def check(data_source):
            s = Subtitle.get_subtitle_from_data_source_dict(data_source)

            ss = []
            for key, value in data_source.items():
                for subtitle in Subtitle.select().where(
                    Subtitle.data_source_id == key,
                    Subtitle.id.in_(value['subtitle_group'].split(','))
                ).dicts():
                    ss.append(subtitle)

            for i in s:
                assert i in ss
            for i in ss:
                assert i in s

        condition = {'mikan_project': {'subtitle_group': ','.join(['1', '2', '6', '7', '9'])}}
        check(condition)

        condition.update({
            'dmhy': {'subtitle_group': ','.join(['37', '552'])},
        })
        check(condition)

        condition.update({
            'bangumi_mod': {
                'subtitle_group': ','.join([
                    '58fe0031e777e29f2a08175d', '567cdf0d3e4e6e4148f19bbd',
                    '567bda4eafc701435d468b61'
                ]),
            }
        })
        check(condition)


class ModelsFunctionTest(TestCase):
    pass
