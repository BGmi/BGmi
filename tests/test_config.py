# coding=utf-8
from __future__ import print_function, unicode_literals

import unittest

import bgmi.config as bgmi_config
from bgmi.lib.controllers import config


class ConfigTest(unittest.TestCase):
    def test_print_config(self):
        r = config()
        self.assertEqual(r['status'], 'info')

    def test_print_single_config(self):
        r = config('DANMAKU_API_URL', '233')

        r = config('DANMAKU_API_URL')
        self.assertEqual(r['status'], 'info')
        self.assertTrue(r['message'].startswith('DANMAKU_API_URL'))
        self.assertTrue(r['message'].endswith('233'))

    def test_readonly(self):
        r = config('DB_PATH', '/tmp/233')
        self.assertEqual(r['status'], 'error')

    def test_writable(self):
        r = config('DANMAKU_API_URL', '233')
        self.assertEqual(r['status'], 'success')
        from bgmi.config import DANMAKU_API_URL
        self.assertEqual(DANMAKU_API_URL, '233')

    def test_source(self):
        r = config('DATA_SOURCE', '233')
        self.assertEqual(r['status'], 'error')

    def test_wrong_config_name(self):
        r = config('WRONG_CONFIG_NAME', '233')
        self.assertEqual(r['status'], 'error')

    # def value_data(self):
    def test_wrong_DOWNLOAD_DELEGATE(self):
        r = config('DOWNLOAD_DELEGATE', 'WRONG_METHOD')
        self.assertEqual(r['status'], 'error')

    def test_DOWNLOAD_DELEGATE(self):
        r = config('DOWNLOAD_DELEGATE', 'aria2-rpc')
        r = config('DOWNLOAD_DELEGATE', 'rr!')
        r = config('WGET_PATH', 'some_place')
        # self.assertEqual(r['status'], 'error')

    @classmethod
    def setUpClass(cls):
        from bgmi.config import CONFIG_FILE_PATH
        import os
        os.remove(CONFIG_FILE_PATH)
        bgmi_config.write_default_config()
        print(os.path.exists(CONFIG_FILE_PATH))
        bgmi_config.read_config()

    # @classmethod
    # def tearDownClass(cls):
    #     bgmi_config.write_default_config()
