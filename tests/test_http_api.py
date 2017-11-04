# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import logging
import os
import random
import string
import unittest

from tornado.testing import AsyncHTTPTestCase

from bgmi.front.server import make_app
from bgmi.main import unicode_

logging.basicConfig(level=logging.DEBUG)


def random_word(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


logger = logging.getLogger()
logger.setLevel(logging.ERROR)
api_list = [
    {
        'action': 'update',
        'method': 'post',
        'params': '{}',
    }, {
        'action': 'status',
        'method': 'post',
        'params': json.dumps({
            'name': os.environ.get('BANGUMI_2'),
            'status': 1,
        }),
    }
]


# DB.recreate_source_relatively_table()


class ApiTestCase(AsyncHTTPTestCase):
    # class ApiTestCase(unittest.TestCase)
    headers = {'BGmi-Token': '233', 'Content-Type': 'application/json'}
    bangumi_1 = unicode_(os.environ.get('BANGUMI_1'))
    bangumi_2 = unicode_(os.environ.get('BANGUMI_2'))
    bangumi_3 = unicode_(os.environ.get('BANGUMI_3'))

    def get_app(self):
        self.app = make_app(debug=False)
        return self.app

    def test_a_auth(self):
        r = self.fetch('/api/auth', method='POST', body=json.dumps({'token': '233'}))
        self.assertEqual(r.code, 200)
        res = self.parse_response(r)
        self.assertEqual(res['status'], 'success')

        r = self.fetch('/api/auth', method='POST', body=json.dumps({'token': '3'}))
        self.assertEqual(r.code, 400)
        res = self.parse_response(r)
        self.assertEqual(res['status'], 'error')

    # def test_a_index(self):
    #     response = self.fetch('/', method='GET')
    #     self.assertEqual(response.code, 404)

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
        elif len(res['data']['subtitle_group']) == 1:
            subtitle_group = res['data']['subtitle_group'][:0]
        else:
            subtitle_group = []
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
        for item in subtitle_group:
            self.assertIn(item, res['data']['followed'])
        for item in res['data']['followed']:
            self.assertIn(item, subtitle_group)

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


if __name__ == '__main__':
    unittest.main()
