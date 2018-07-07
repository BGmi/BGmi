# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import logging
import os
import random
import string

from tornado.testing import AsyncHTTPTestCase

from bgmi.config import SAVE_PATH, ADMIN_TOKEN
from bgmi.front.server import make_app
from bgmi.lib.constants import unicode_

logging.basicConfig(level=logging.DEBUG)


def random_word(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class ApiTestCase(AsyncHTTPTestCase):
    headers = {'BGmi-Token': ADMIN_TOKEN, 'Content-Type': 'application/json'}
    bangumi_1 = unicode_(os.environ.get('BANGUMI_1'))
    bangumi_2 = unicode_(os.environ.get('BANGUMI_2'))
    bangumi_3 = unicode_(os.environ.get('BANGUMI_3'))

    def get_app(self):
        self.app = make_app(debug=False)
        return self.app

    def test_a_auth(self):
        r = self.fetch('/api/auth', method='POST', body=json.dumps({'token': ADMIN_TOKEN}))
        self.assertEqual(r.code, 200)
        res = self.parse_response(r)
        self.assertEqual(res['status'], 'success')

        r = self.fetch('/api/auth', method='POST', body=json.dumps({'token': '3'}))
        self.assertEqual(r.code, 400)
        res = self.parse_response(r)
        self.assertEqual(res['status'], 'error')

    def test_a_cal(self):
        r = self.fetch('/api/cal', method='GET')
        res = self.parse_response(r)
        self.assertIsInstance(res['data'], dict)

    def test_b_add(self):
        r = self.fetch('/api/add', method='POST',
                       headers=self.headers,
                       body=json.dumps({
                           'name': self.bangumi_1,
                       }))
        self.assertEqual(r.code, 200)

        r = self.fetch('/api/add', method='POST',
                       headers=self.headers,
                       body=json.dumps({
                           'name': self.bangumi_1,
                       }))
        self.assertEqual(r.code, 200)
        r = self.parse_response(r)
        self.assertEqual(r['status'], 'warning')

        r = self.fetch('/api/add', method='POST',
                       headers=self.headers,
                       body=json.dumps({
                           'name': self.bangumi_2,
                       }))
        self.assertEqual(r.code, 200)

    def test_c_delete(self):
        r = self.fetch('/api/add', method='POST',
                       headers=self.headers,
                       body=json.dumps({
                           'name': self.bangumi_2,
                       }))
        self.assertEqual(r.code, 200)
        r = self.parse_response(r)
        self.assertEqual(r['status'], 'warning')

        r = self.fetch('/api/add', method='POST',
                       headers=self.headers,
                       body=json.dumps({
                           'name': self.bangumi_2,
                       }))
        self.assertEqual(r.code, 200)
        r = self.parse_response(r)
        self.assertEqual(r['status'], 'warning')

        r = self.fetch('/api/add', method='POST',
                       headers=self.headers,
                       body=json.dumps({
                           'name': self.bangumi_2,
                       }))
        self.assertEqual(r.code, 200)
        r = self.parse_response(r)
        self.assertEqual(r['status'], 'warning')

    def test_e_mark(self):
        episode = random.randint(0, 10)
        self.fetch('/api/mark', method='POST', headers=self.headers,
                   body=json.dumps({
                       "name": self.bangumi_1,
                       "episode": episode
                   }))
        r = self.fetch('/api/index', method='GET')
        self.assertEqual(r.code, 200)
        res = self.parse_response(r)
        bg_dict = {}
        for item in res['data']:
            if item['bangumi_name'] == self.bangumi_1:
                bg_dict = item
                break
        self.assertEqual(bg_dict['bangumi_name'], self.bangumi_1)
        self.assertEqual(bg_dict['episode'], episode)

    def test_d_filter(self):
        include = random_word(5)
        exclude = random_word(5)
        regex = random_word(5)

        r = self.fetch('/api/filter', method='POST', body=json.dumps({
            'name': self.bangumi_1,
        }), headers=self.headers)

        self.assertEqual(r.code, 200)
        res = self.parse_response(r)
        self.assertEqual(res['status'], 'success')

        if len(res['data']['subtitle_group']) >= 2:
            subtitle_group = res['data']['subtitle_group'][:1]
        else:
            subtitle_group = res['data']['subtitle_group'][:0]
        subtitle = ','.join(subtitle_group)

        r = self.fetch('/api/filter', method='POST', body=json.dumps({
            'name': self.bangumi_1,
            'include': include,
            'regex': regex,
            'exclude': exclude,
            'subtitle': subtitle,
        }), headers=self.headers)
        r = self.fetch('/api/filter', method='POST', body=json.dumps({
            'name': self.bangumi_1,
        }), headers=self.headers)

        res = self.parse_response(r)

        self.assertEqual(r.code, 200)
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['data']['name'], self.bangumi_1)
        self.assertEqual(res['data']['include'], include)
        self.assertEqual(res['data']['regex'], regex)
        self.assertEqual(res['data']['exclude'], exclude)

        r = self.fetch('/api/filter', method='POST', body=json.dumps({
            'name': self.bangumi_3,
            'regex': '.*',
            'subtitle': '',
        }), headers=self.headers)
        self.assertEqual(r.code, 400)
        self.assertEqual(self.parse_response(r)['status'], 'error')
        print(subtitle_group)
        self.assertFalse(bool(list(set(subtitle_group) - set(res['data']['followed']))))
        # for item in subtitle_group:
        #     self.assertIn(item, res['data']['followed'])
        # for item in res['data']['followed']:
        #     self.assertIn(item, subtitle_group)

    def test_e_index(self):
        save_dir = os.path.join(SAVE_PATH)
        episode1_dir = os.path.join(save_dir, self.bangumi_1, '1', 'episode1')
        if not os.path.exists(episode1_dir):
            os.makedirs(episode1_dir)
        open(os.path.join(episode1_dir, '1.mp4'), 'a').close()

        episode2_dir = os.path.join(save_dir, self.bangumi_1, '2')
        if not os.path.exists(episode2_dir):
            os.makedirs(episode2_dir)
        open(os.path.join(episode2_dir, '2.mkv'), 'a').close()

        response = self.fetch('/api/index', method='GET')
        self.assertEqual(response.code, 200)
        r = self.parse_response(response)
        episode_list = [x for x in r['data'] if x["bangumi_name"] == self.bangumi_1]
        bangumi_dict = next(iter(episode_list or []), {})

        self.assertIn('1', bangumi_dict['player'].keys())
        self.assertEqual(bangumi_dict['player']['1']['path'], '/{}/1/episode1/1.mp4'.format(self.bangumi_1))
        self.assertIn('2', bangumi_dict['player'].keys())
        self.assertEqual(bangumi_dict['player']['2']['path'], '/{}/2/2.mkv'.format(self.bangumi_1))

    def test_resource_ics(self):
        r = self.fetch('/resource/feed.xml')
        self.assertEqual(r.code, 200)

    def test_resource_feed(self):
        r = self.fetch('/resource/calendar.ics')
        self.assertEqual(r.code, 200)

    def test_no_auth(self):
        r = self.fetch('/api/add', method='POST', body=json.dumps({'name': self.bangumi_1}))
        self.assertEqual(r.code, 401)

    @staticmethod
    def parse_response(response):
        r = json.loads(response.body.decode('utf-8'))
        return r
