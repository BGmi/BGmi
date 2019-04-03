# coding=utf-8
import time
from unittest import TestCase
from unittest.mock import patch, Mock

import faker

import bgmi.config
import bgmi.lib.models
from bgmi.lib import models
from bgmi.lib.models import Subtitle, Bangumi, Followed
from bgmi.sql import init_db

test_data = {}


class base():
    faker = faker.Faker()

    def setUp(self):
        bgmi.lib.models.recreate_source_relatively_table()

    @staticmethod
    def setUpClass():
        init_db()
        pass

    @staticmethod
    def tearDownClass():
        pass


class BangumiTest(base, TestCase):
    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def test__init__(self, **kwargs):
        self.assertRaises(ValueError, lambda: Bangumi(update_time='wrong'))
        query = {
            'update_time': 'wed',
            'subtitle_group': ['1', '2', '3']
        }
        b = Bangumi(**query)
        self.assertEqual(b.update_time, 'Wed')
        self.assertIn(b.update_time, b.update_time)
        self.assertEqual(b.subtitle_group, ['1', '2', '3'])

    #
    """
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)
    """
    """
    class Bangumi(NeoDB):
        id = IntegerField(primary_key=True)
        name = TextField(unique=True, null=False)
        update_time = FixedCharField(5, null=False)
        keyword = TextField()
        status = IntegerField(default=0)
        cover = TextField()
        type = TextField(null=False)
        data_source = JSONField(default=lambda: {})  # type: dict
    """

    def test_delete_all(self):
        now = int(time.time())
        name_updating = []
        for i in range(5):
            name = self.faker.name()
            Bangumi.create(name=name, keyword=name, cover=name, update_time='mon', status=Bangumi.STATUS.UPDATING)
            Followed.create(bangumi_name=name, updated_time=now + i)
            name_updating.append(name)

        name_end = []
        for i in range(5):
            name = self.faker.name()
            Bangumi.create(name=name, keyword=name, cover=name, update_time='mon',
                           status=models.Bangumi.STATUS.UPDATING)
            Followed.create(bangumi_name=name, updated_time=now - 2 * 2 * 7 * 24 * 3600 - 200)
            name_end.append(name)

        Bangumi.delete_all()

        for bangumi in Bangumi.select().where(Bangumi.name.in_(name_updating)):
            self.assertEqual(bangumi.status, models.Bangumi.STATUS.UPDATING)

        for bangumi in Bangumi.select().where(Bangumi.name.in_(name_end)):
            self.assertEqual(bangumi.status, models.Bangumi.STATUS.END)

    def test_get_updating_bangumi(self):
        bgm_followed = []
        for day in Bangumi.week:
            name = self.faker.name()
            bangumi = Bangumi.create(name=name, keyword=name, cover=name, update_time=day, status=models.Followed.STATUS.DELETED)
            Followed.create(bangumi_name=name, status=Followed.STATUS.FOLLOWED)
            bgm_followed.append(name)

        bgm_updated = []
        for day in Bangumi.week:
            name = self.faker.name()
            bangumi = Bangumi.create(name=name, keyword=name, cover=name, update_time=day,
                                     status=Bangumi.STATUS.UPDATING)
            Followed.create(bangumi_name=name, status=Followed.STATUS.UPDATED)
            bgm_updated.append(name)

        b1 = Bangumi.get_updating_bangumi(status=Followed.STATUS.FOLLOWED, order=True)
        b2 = Bangumi.get_updating_bangumi(status=Followed.STATUS.UPDATED, order=True)
        b3 = Bangumi.get_updating_bangumi(order=False)

        for key, value in b1.items():
            self.assertIn(key.title(), Bangumi.week)
            for bangumi in value:
                self.assertIn(bangumi['name'], bgm_followed)

        for key, value in b2.items():
            self.assertIn(key.title(), Bangumi.week)
            self.assertFalse(list())
            for v in value:  #
                self.assertIn(v['name'], bgm_updated)

        for bangumi in b3:
            self.assertIn(bangumi['name'], bgm_followed + bgm_updated)

    def test_get_all_bangumi(self):
        Bangumi.delete().execute()

        Bangumi.create(name='name', cover='name', update_time='mon', status=Bangumi.STATUS.UPDATING)
        b = Bangumi.get_all_bangumi()
        for bg in b:
            self.assertEqual(bg['name'], 'name')
            self.assertEqual(bg['subject_name'], 'name')
            self.assertEqual(bg['cover'], 'name')


class FollowedTest(base, TestCase):

    def test_delete_followed(self):
        name = self.faker.name()
        Followed.create(bangumi_name=name)
        with patch('builtins.input', Mock(return_value='n')) as m:
            Followed.delete_followed(batch=False)
            m.assert_any_call('[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ')
            m.return_value = 'y'
            Followed.delete_followed(batch=False)
        self.assertFalse(Followed.select())

    def test_get_all_followed(self):
        Followed.get_all_followed()


import json

with open('tests/data/subtitle.json', 'r', encoding='utf8')as f:
    subtitle_group = json.load(f)
    for key, value in subtitle_group.items():
        for subtitle in value:
            subtitle['data_source'] = key
subtitle_list = []
for key, value in subtitle_group.items():
    subtitle_list += value


class SubtitleTest(TestCase):

    def setUp(self):
        Subtitle.insert_many(subtitle_list).execute()

    def tearDown(self):
        Subtitle.delete().execute()

    def test_get_subtitle_of_bangumi(self):
        """

        :type bangumi_obj: Bangumi
        """
        pass
        r = [{'123': '456'}]

        class B(Bangumi):
            data_source = {'dmhy': {}}

        with patch('bgmi.lib.models.Subtitle.get_subtitle_from_data_source_dict', Mock(return_value=r)) as m:
            Subtitle.get_subtitle_of_bangumi(B())
            m.assert_called_with({'dmhy': {}})

    def test_get_subtitle_from_data_source_dict(self):
        """
        :type data_source: dict
        :param data_source:
        :return:
        """

        def check(data_source):
            s = Subtitle.get_subtitle_from_data_source_dict(data_source)

            # All subtitles meet the requirement
            for subtitle in subtitle_list:
                for key, value in data_source.items():
                    if key == subtitle['data_source'] and subtitle['id'] in value['subtitle_group']:
                        self.assertIn(subtitle, s)

            # No extra subtitle returned
            for subtitle in s:
                self.assertIn(subtitle, subtitle_group[subtitle['data_source']])
                self.assertIn(subtitle['id'], data_source[subtitle['data_source']]['subtitle_group'])

        condition = {'mikan_project': {'subtitle_group': ['1', '2', '6', '7', '9']}}
        check(condition)

        condition.update({'dmhy': {"subtitle_group": ["37", "552"]}, })
        check(condition)

        condition.update({"bangumi_mod": {
            "subtitle_group": ["58fe0031e777e29f2a08175d", "567cdf0d3e4e6e4148f19bbd", "567bda4eafc701435d468b61"], }})
        check(condition)
