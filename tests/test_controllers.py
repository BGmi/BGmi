import unittest
from unittest import mock

import bgmi.lib.controllers
from bgmi.lib import controllers
from bgmi.lib.controllers import ControllerResult
from bgmi.lib.models import Bangumi, Followed
from bgmi.website.base import BaseWebsite
from tests.test_models import Base


def w():
    return mock.Mock(spec=BaseWebsite)


class ControllersTest(Base, unittest.TestCase):
    """
    at the beginning of each test,
    bangumi 1 is followed
    bangumi 2 is not followed
    """
    bangumi_name_1 = '机动奥特曼'  # not followed bangumi
    bangumi_name_2 = '海贼王'  # followed bangumi

    def get_followed_obj(self):
        return Followed.get_by_name(bangumi_name=self.bangumi_name_2)

    def test_cal(self):
        r = bgmi.lib.controllers.cal()
        self.assertIsInstance(r, dict)
        for day in r.keys():
            self.assertIn(day.lower(), [x.lower() for x in Bangumi.week])
            self.assertIsInstance(r[day], list)
            for bangumi in r[day]:
                # {'bangumi_name': 'TEST_BANGUMI', 'cover': '', 'update_time': 'Mon',
                #  'name': 'TEST_BANGUMI', 'status': 1,
                #  'updated_time': 0, 'subtitle_group': '', 'episode': 0}
                for key in ['name', 'cover', 'update_time', 'status', 'episode']:
                    self.assertIn(key, bangumi)

    def test_add(self):
        r = bgmi.lib.controllers.add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')

        f = Followed.get_by_name(bangumi_name=self.bangumi_name_1)  # type: Followed
        self.assertEqual(f.status, Followed.STATUS.FOLLOWED)

    def test_add_dupe_warning(self):
        r = bgmi.lib.controllers.add(self.bangumi_name_2, 0)
        self.assertEqual(r['status'], 'warning')

        f = Followed.get_by_name(bangumi_name=self.bangumi_name_2)  # type: Followed
        self.assertEqual(f.status, Followed.STATUS.FOLLOWED)

    def test_add_with_episode(self):

        r = bgmi.lib.controllers.add(self.bangumi_name_1, episode=4)
        self.assertEqual(r['status'], 'success')
        f = Followed.get_by_name(bangumi_name=self.bangumi_name_1)  # type: Followed
        self.assertEqual(f.status, Followed.STATUS.FOLLOWED)
        self.assertEqual(f.episode, 4)

    def test_mark(self):
        r = bgmi.lib.controllers.mark(self.bangumi_name_2, 1)
        self.assertEqual(r['status'], 'success', r['message'])
        r = bgmi.lib.controllers.mark(self.bangumi_name_2, None)
        self.assertEqual(r['status'], 'info')
        r = bgmi.lib.controllers.mark(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'error', r['message'])

    def test_delete(self):
        r = bgmi.lib.controllers.delete()
        self.assertEqual(r['status'], 'warning')
        r = bgmi.lib.controllers.delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'error', r['message'])
        # r = bgmi.lib.controllers.delete(self.bangumi_name_1)
        # self.assertEqual(r['status'], 'warning')
        r = bgmi.lib.controllers.delete(self.bangumi_name_2)
        self.assertEqual(r['status'], 'warning', r['message'])
        r = bgmi.lib.controllers.delete(clear_all=True, batch=True)
        self.assertEqual(r['status'], 'warning')

    def test_search(self):
        bgmi.lib.controllers.search(self.bangumi_name_1, dupe=False)

    def test_filter_name_not_exists(self):
        """

        :return:
        """

        result = controllers.filter_(name='hello')
        self.assertEqual(
            result.status,
            ControllerResult.error,
            'non existed bangumi should return {}'.format(ControllerResult.error),
        )

        result = controllers.filter_(name=self.bangumi_name_1)
        self.assertEqual(
            result.status,
            ControllerResult.error,
            'non followed bangumi should return {}'.format(ControllerResult.error),
        )

        result = controllers.filter_(name=self.bangumi_name_2)
        self.assertEqual(
            result.status,
            ControllerResult.success,
            'non followed bangumi should return {}'.format(ControllerResult.success),
        )

    valid_subtitle = 'OPFans枫雪动漫'
    invalid_subtitle = '红烧鱼字幕组'
    not_a_subtitle = 'hello world'

    def test_filter_subtitle_input_not_exist(self):
        """
        {
            'name': '海贼王',
            'data_source': ['mikan_project', 'bangumi_moe', 'dmhy'],
            'subtitle_group': ['OPFans枫雪动漫', '天空树双语字幕组', 'Dymy字幕组']
        }
        """

        result = controllers.filter_(name=self.bangumi_name_2, subtitle_input=self.not_a_subtitle)
        self.assertEqual(
            result.status,
            ControllerResult.error,
            'unavailable subtitle_group should return {}'.format(ControllerResult.error),
        )

        result = controllers.filter_(self.bangumi_name_2)
        self.assertFalse(result.data['followed'])

    def test_filter_subtitle_input_not_available(self):

        result = controllers.filter_(name=self.bangumi_name_2, subtitle_input=self.invalid_subtitle)
        self.assertEqual(
            result.status,
            ControllerResult.error,
            'unavailable subtitle_group should return {}'.format(ControllerResult.error),
        )

        result = controllers.filter_(self.bangumi_name_2)
        self.assertFalse(result.data['followed'])

    def test_filter_add_right_subtitle(self):
        result = controllers.filter_(name=self.bangumi_name_2, subtitle_input=self.valid_subtitle)
        self.assertEqual(result.status, ControllerResult.success)
        self.assertEqual(result.data['followed'], [self.valid_subtitle])

        followed_obj = Followed.get_by_name(bangumi_name=self.bangumi_name_2)
        self.assertEqual(followed_obj.subtitle, [self.valid_subtitle])

        result = controllers.filter_(self.bangumi_name_2)
        self.assertEqual(result.data['followed'], [self.valid_subtitle])

    valid_data_source = 'mikan_project'
    invalid_data_source = 'dmhy'
    not_a_data_source = 'hello world'

    def test_data_source_input_not_available(self):
        result = controllers.filter_(
            name=self.bangumi_name_2,
            data_source_input=self.invalid_data_source,
        )
        self.assertEqual(result.status, ControllerResult.error, result.message)

        followed_obj = Followed.get_by_name(bangumi_name=self.bangumi_name_2)
        self.assertEqual(followed_obj.data_source, [])

        result = controllers.filter_(self.bangumi_name_2)
        self.assertEqual(
            result.data['followed_data_source'],
            [],
            result.message,
        )

    def test_data_valid_data_source(self):
        result = controllers.filter_(
            name=self.bangumi_name_2,
            data_source_input=self.valid_data_source,
        )
        self.assertEqual(result.status, ControllerResult.success, result.message)
        self.assertEqual(
            result.data['followed_data_source'],
            [self.valid_data_source],
            result.message,
        )

        followed_obj = Followed.get_by_name(bangumi_name=self.bangumi_name_2)
        self.assertEqual(followed_obj.data_source, [self.valid_data_source])

        result = controllers.filter_(self.bangumi_name_2)
        self.assertEqual(
            result.data['followed_data_source'],
            [self.valid_data_source],
            result.message,
        )

    def test_data_include_with_space(self):
        v = ['1', '2', '3', '4', '5']
        value = ','.join(v)
        result = controllers.filter_(
            name=self.bangumi_name_2,
            include=value,
        )
        self.assertEqual(
            result.status,
            ControllerResult.success,
            'include value {}'.format(value),
        )
        self.assertEqual(result.data['include'], v)
        followed_obj = self.get_followed_obj()
        self.assertEqual(followed_obj.include, v, 'include value should be parsed saved')

    def test_data_exclude_with_space(self):
        v = ['1', '2', '3', '4', '5']
        value = ','.join(v)
        result = controllers.filter_(
            name=self.bangumi_name_2,
            exclude=value,
        )
        self.assertEqual(result.status, ControllerResult.success, value)
        self.assertEqual(result.data['exclude'], v)
        followed_obj = self.get_followed_obj()
        self.assertEqual(followed_obj.exclude, v, 'exclude value should be parsed and saved')

    def test_data_regex(self):
        value = r'1 2\ 23 \\1233123'
        result = controllers.filter_(
            name=self.bangumi_name_2,
            regex=value,
        )
        self.assertEqual(result.status, ControllerResult.success, value)
        self.assertEqual(result.data['regex'], value)
        followed_obj = self.get_followed_obj()
        self.assertEqual(followed_obj.regex, value, 'regex value should be saved')

    def test_data_regex_set_none(self):
        result = controllers.filter_(self.bangumi_name_2, regex='')
        self.assertEqual(result.data['regex'], '')

    def test_data_include_set_none(self):
        result = controllers.filter_(self.bangumi_name_2, include='')
        self.assertEqual(result.data['include'], None)

    def test_data_exclude_set_none(self):
        result = controllers.filter_(self.bangumi_name_2, exclude='')
        self.assertEqual(result.data['exclude'], None)
