import json
import time
from os import path
from unittest import TestCase
from unittest.mock import Mock, patch

import faker

from bgmi.lib import db_models
from bgmi.lib.db_models import Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle, db
from tests.base import project_dir

with open(
    path.join(project_dir, 'tests/data/db_models/main_bangumi.json'), 'r', encoding='utf8'
) as f:
    bangumi_list = json.load(f)
with open(
    path.join(project_dir, 'tests/data/db_models/main_followed.json'), 'r', encoding='utf8'
) as f:
    followed_list = json.load(f)
with open(
    path.join(project_dir, 'tests/data/db_models/main_bangumi_item.json'), 'r', encoding='utf8'
) as f:
    bangumi_item_list = json.load(f)

with open(path.join(project_dir, 'tests/data/db_models/subtitle.json'), 'r', encoding='utf8') as f:
    subtitle_group = json.load(f)
    for key, value in subtitle_group.items():
        for subtitle in value:
            subtitle['data_source'] = key
subtitle_list = []
for _, value in subtitle_group.items():
    subtitle_list += value

# with open(path.join(project_dir, 'tests/data/db_models/main_subtitle.json'),
#           'r', encoding='utf8') as f:
#     subtitle_list = json.load(f)


class Base:
    faker = faker.Faker()

    def setUp(self):
        db.create_tables([Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle])
        Bangumi.delete().where(True).execute()
        Followed.delete().where(True).execute()
        BangumiItem.delete().where(True).execute()
        Subtitle.delete().where(True).execute()
        # db.create_tables([Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle])
        Bangumi.insert_many(bangumi_list).execute()
        BangumiItem.insert_many(bangumi_item_list).execute()
        Subtitle.insert_many(subtitle_list).execute()
        Followed.insert_many(followed_list).execute()
        db.close()

    # def tearDown(self):
    #     db.drop_tables([
    #         Bangumi,
    #         Followed,
    #         Download,
    #         Subtitle,
    #         BangumiItem,
    #         BangumiLink,
    #         Scripts,
    #     ])


class BangumiTest(Base, TestCase):
    week = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

    def test__init__(self, **kwargs):
        self.assertRaises(ValueError, lambda: Bangumi(update_time='wrong'))
        query = {'update_time': 'wed', 'subtitle_group': ['1', '2', '3']}
        b = Bangumi(**query)
        self.assertEqual(b.update_time, 'Wed')
        self.assertIn(b.update_time, b.week)
        self.assertEqual(b.subtitle_group, ['1', '2', '3'])

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

        for bangumi in b3:
            self.assertIn(bangumi['name'], [
                '机动奥特曼',
                '川柳少女',
                '名侦探柯南',
                '海贼王',
                '汉化日记',
            ])

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
                self.assertIn(
                    subtitle['id'], data_source[subtitle['data_source']]['subtitle_group']
                )

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
