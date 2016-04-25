# coding=utf-8
from __future__ import print_function, unicode_literals
import unittest
from bgmi.fetch import parser_bangumi, process_subtitle, parse_episode, get_maximum_episode


class BangumiTest(unittest.TestCase):
    def setUp(self):
        import os
        with open(os.path.join(os.path.dirname(__file__), 'programme.html')) as f:
            self.bangumi_data = f.read()

    def test_process_subtitle(self):
        test_data = '<a href="/topics/list?keyword=%E7%88%86%E9%9F%B3%E5%B0%91%E5%A5%B3%7Cbakuon+t' \
                    'eam_id%3A533">花語</a><a href="/topics/list?keyword=%E7%88%86%E9%9F%B3%E5%B0%' \
                    '91%E5%A5%B3%7Cbakuon+team_id%3A459">紫音</a><a href="/topics/list?keyword=%E7' \
                    '%88%86%E9%9F%B3%E5%B0%91%E5%A5%B3%7Cbakuon+team_id%3A533"></a>'
        ret_data = process_subtitle(test_data)
        self.assertEqual(['花語', '紫音'], ret_data)

    def test_parse_bangumi(self):
        result = parser_bangumi(self.bangumi_data)
        self.assertEqual(sum(map(len, result.values())), 71)

    def test_parse_episode(self):
        self.assertEqual(2, parse_episode('[Mabors Sub] Sakamoto Desu ga - 02 [GB][720P][PSV&PC]'))
        self.assertEqual(12, parse_episode('[啊啊字幕组] [在下坂本,有何贵干][12][GB][720P][PSV&PC]'))

    def test_get_maximum_episode(self):
        # Deprecated test

        # data = [{'episode': 12, 'title': 'A'}, {'episode': 11, 'title': 'B'}]
        # self.assertEqual(get_maximum_episode(data)['episode'], 12)

        # data = [{'episode': None, 'title': 'A'}, {'episode': None, 'title': 'B'}]
        # self.assertEqual(get_maximum_episode(data), None)
        pass


if __name__ == '__main__':
    unittest.main()
