# coding=utf-8
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

        assert_data = [{'status': 0, 'update_time': 'wed', 'keyword': '%E9%8A%80%E9%AD%82%7CGintama',
                        'name': '\xe9\x8a\x80\xe9\xad\x82',
                        'subtitle_group': ['\xe5\x8b\x95\xe6\xbc\xab\xe8\x8a\xb1\xe5\x9c\x92',
                                           '\xe7\x95\xb0\xe5\x9f\x9f', '\xe8\xb1\x8c\xe8\xb1\x86',
                                           '\xe6\x97\x8b\xe9\xa2\xa8', '\xe6\xa5\xb5\xe5\xbd\xb1',
                                           '\xe5\x95\x9f\xe8\x90\x8c']},
                       {'status': 0, 'update_time': 'wed', 'keyword': '%E8%96%84%E6%AB%BB+%E5%BE%A1%E4%BC%BD',
                        'name': '\xe8\x96\x84\xe6\xab\xbb\xe9\xac\xbc\xef\xbd\x9e\xe5\xbe\xa1'
                                '\xe4\xbc\xbd\xe8\x8d\x89\xe5\xad\x90\xef\xbd\x9e',
                        'subtitle_group': ['\xe5\xb9\xbb\xe4\xb9\x8b', '\xe7\x95\xb0\xe5\x9f\x9f', 'WOLF',
                                           '\xe6\xa5\xb5\xe5\xbd\xb1']},
                       {'status': 0, 'update_time': 'wed', 'keyword': 'Joker+Game',
                        'name': '\xe9\xac\xbc\xe7\x89\x8c\xe9\x81\x8a\xe6\x88\xb2',
                        'subtitle_group': ['\xe5\x8b\x95\xe6\xbc\xab\xe5\x9c\x8b', 'RH', '\xe7\xb4\xab\xe9\x9f\xb3',
                                           '\xe8\xbf\xbd\xe6\x94\xbe', 'WOLF', '\xe8\xab\xb8\xe7\xa5\x9e',
                                           '\xe6\x83\xa1\xe9\xad\x94\xe5\xb3\xb6']},
                       {'status': 0, 'update_time': 'wed', 'keyword': '%E6%88%B0%E9%AC%A5%E4%B9%8B%E9%AD%82',
                        'name': '\xe6\x88\xb0\xe9\xac\xa5\xe4\xb9\x8b\xe9\xad\x82 \xe9\x9b\x99'
                                '\xe9\x87\x8d\xe9\xa9\x85\xe5\x8b\x95',
                        'subtitle_group': []},
                       {'status': 0, 'update_time': 'wed', 'keyword': '%E9%9B%99%E6%98%9F+%E9%99%B0%E9%99%BD',
                        'name': '\xe9\x9b\x99\xe6\x98\x9f\xe4\xb9\x8b\xe9\x99\xb0\xe9\x99\xbd\xe5\xb8\xab',
                        'subtitle_group': ['\xe6\x83\xa1\xe9\xad\x94\xe5\xb3\xb6', '\xe6\xa5\xb5\xe5\xbd\xb1', 'TU']},
                       {'status': 0, 'update_time': 'wed', 'keyword': '%E8%B2%93%E8%B2%93%E6%97%A5%E6%9C%AC%E5%8F%B2',
                        'name': '\xe8\xb2\x93\xe8\xb2\x93\xe6\x97\xa5\xe6\x9c\xac\xe5\x8f\xb2',
                        'subtitle_group': ['WOLF']}]

        self.assertEqual(result['wed'], assert_data)

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
