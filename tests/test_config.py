# coding=utf-8

import configparser
import os
import unittest
import unittest.mock
from unittest.mock import patch, Mock

import bgmi.config
from bgmi.config import write_default_config, CONFIG_FILE_PATH
from bgmi.lib.controllers import config


class base():
    def setUp(self):
        os.remove(CONFIG_FILE_PATH) if os.path.exists(CONFIG_FILE_PATH) else None

        write_default_config()
        self.config = configparser.ConfigParser()
        self.read = lambda: self.config.read(CONFIG_FILE_PATH)

        def w():
            with open(CONFIG_FILE_PATH, 'w', encoding='utf8') as f:
                self.config.write(f)

        self.write = w

    @staticmethod
    def setUpClass():
        os.remove(CONFIG_FILE_PATH) if os.path.exists(CONFIG_FILE_PATH) else None
        write_default_config()

    @staticmethod
    def tearDownClass():
        os.remove(CONFIG_FILE_PATH) if os.path.exists(CONFIG_FILE_PATH) else None
        write_default_config()


class WriteConfigTest(base, unittest.TestCase):

    def test_get_bgmi_path(self):
        with patch('bgmi.config.platform.system', Mock(return_value='Windows')):
            raw_home = os.environ['USERPROFILE']
            os.environ['USERPROFILE'] = 'windows profile'
            self.assertEqual(bgmi.config.get_bgmi_path(), os.path.join('windows profile', '.bgmi'))
            os.environ['USERPROFILE'] = raw_home

        with patch('bgmi.config.platform.system', Mock(return_value='Linux')):
            raw_home = os.environ['HOME']
            os.environ['HOME'] = 'linux profile'
            self.assertEqual(bgmi.config.get_bgmi_path(), os.path.join('linux profile', '.bgmi'))
            os.environ['HOME'] = raw_home

    def test_wrong_config_value(self):
        bgmi.config.ADMIN_TOKEN = None
        write_default_config()
        bgmi.config.DOWNLOAD_DELEGATE = 'wrong'
        self.assertRaises(Exception, write_default_config)
        bgmi.config.DOWNLOAD_DELEGATE = 'aria2-rpc'

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
        self.assertEqual(bgmi.config.DANMAKU_API_URL, '233')

    def test_not_writable(self):
        r = config('DAN_API_URL', '233')

    def test_source(self):
        r = config('DATA_SOURCE', '233')
        self.assertEqual(r['status'], 'error')

    def test_wrong_config_name(self):
        r = config('WRONG_CONFIG_NAME', '233')
        self.assertEqual(r['status'], 'error')

    # def value_data(self):
    def test_set_wrong_DOWNLOAD_DELEGATE(self):
        r = config('DOWNLOAD_DELEGATE', 'WRONG_METHOD')
        self.assertEqual(r['status'], 'error')

    def test_DOWNLOAD_DELEGATE(self):
        r = config('DOWNLOAD_DELEGATE', 'aria2-rpc')
        r = config('DOWNLOAD_DELEGATE', 'rr!')
        r = config('WGET_PATH', 'some_place')
        # self.assertEqual(r['status'], 'error')

    def test_DOWNLOAD_DELEGATE_VALUE(self):
        r = config('DOWNLOAD_DELEGATE', 'aria2-rpc')
        r = config('ARIA2_RPC_URL', 'some_place')
        self.assertEqual(r['status'], 'success')
        self.assertEqual(r['message'], 'ARIA2_RPC_URL has been set to some_place')
        self.read()
        self.assertEqual(self.config.get('aria2-rpc', 'ARIA2_RPC_URL'), 'some_place')

    def test_get_DOWNLOAD_DELEGATE_VALUE(self):
        r = config('ARIA2_RPC_URL')
        self.assertEqual(r['status'], 'info')
        self.assertEqual(r['message'], 'ARIA2_RPC_URL=http://localhost:6800/rpc')


class BadConfigTest(base, unittest.TestCase):
    def test_bad_config_file_missing_options(self):
        # os.remove(CONFIG_FILE_PATH)
        self.read()
        self.config.remove_option('bgmi', 'MAX_PAGE')
        self.write()
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            r = config('MAX_PAGE')
            self.assertEqual(r['status'], 'error')
            m.assert_any_call()

    def test_bad_config_file_missing_section(self):
        # os.remove(CONFIG_FILE_PATH)
        self.read()
        self.config.remove_section('bgmi')
        self.write()
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            r = config()
            self.assertEqual(r['status'], 'error')
            m.assert_any_call()

    def test_bad_config_file_missing_file(self):
        os.remove(CONFIG_FILE_PATH)
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            bgmi.config.read_config()
            m.assert_any_call()

    def test_config_file_not_exist(self):
        os.remove(CONFIG_FILE_PATH)
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            r = config()
            m.assert_any_call()
        # write_default_config()
