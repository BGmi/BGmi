import configparser
import os
import unittest
import unittest.mock
from unittest.mock import patch

import pytest

import bgmi.config
import bgmi.config_utils
from bgmi.config import CONFIG_FILE_PATH, write_default_config
from bgmi.lib.constants import ActionStatus
from bgmi.lib.controllers import config_
from bgmi.models.config import get_bgmi_path


class base:
    def setUp(self):
        try:
            os.makedirs(bgmi.config.config_obj.BGMI_PATH)
        except FileExistsError:
            pass

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
        if os.path.exists(CONFIG_FILE_PATH):
            os.remove(CONFIG_FILE_PATH)
        write_default_config()


class ReadConfigTest(base, unittest.TestCase):
    def setUp(self):
        try:
            os.makedirs(bgmi.config.config_obj.BGMI_PATH)
        except FileExistsError:
            pass

        os.remove(CONFIG_FILE_PATH) if os.path.exists(CONFIG_FILE_PATH) else None

    @staticmethod
    def setUpClass():
        os.remove(CONFIG_FILE_PATH) if os.path.exists(CONFIG_FILE_PATH) else None
        write_default_config()

    @staticmethod
    def tearDownClass():
        if os.path.exists(CONFIG_FILE_PATH):
            os.remove(CONFIG_FILE_PATH)
        write_default_config()

    def test_gbk_config_file(self):
        with open(CONFIG_FILE_PATH, 'w', encoding='gbk') as f:
            f.write(
                '''[bgmi]
bangumi_moe_url = https://bangumi.moe
save_path = /tmp/bangumi
download_delegate = aria2-rpc
max_page = 3
tmp_path = /tmp/bgmi/tmp
danmaku_api_url =
disabled_data_source =
lang = zh_cn
admin_token = 233
share_dmhy_url = https://share.dmhy.org
global_filter = Leopard-Raws, hevc, x265, c-a Raws, 预告
enable_global_filter = 1
tornado_serve_static_files = 1

aria2_rpc_url = http://localhost:6800/rpc
aria2_rpc_token = token:
'''
            )
        cfg = bgmi.config.read_config()
        self.assertEqual(cfg.ADMIN_TOKEN, '233')

    def test_utf8_config_file(self):
        with open(CONFIG_FILE_PATH, 'w+', encoding='utf8') as f:
            f.write(
                '''[bgmi]
bangumi_moe_url = https://bangumi.moe
save_path = /tmp/bangumi
download_delegate = aria2-rpc
max_page = 3
tmp_path = /tmp/bgmi/tmp
danmaku_api_url =
disabled_data_source =
lang = zh_cn
admin_token = 233
share_dmhy_url = https://share.dmhy.org
global_filter = Leopard-Raws, hevc, x265, c-a Raws, 预告
enable_global_filter = 1
tornado_serve_static_files = 1

aria2_rpc_url = http://localhost:6800/rpc
aria2_rpc_token = token:
'''
            )
        cfg = bgmi.config.read_config()
        assert cfg.ADMIN_TOKEN == '233'


class WriteConfigTest(base, unittest.TestCase):
    def test_get_bgmi_path(self):
        old_bgmi_path = os.environ.get('BGMI_PATH', None)
        if old_bgmi_path:
            del os.environ['BGMI_PATH']

        raw_home = os.environ.get('HOME')
        os.environ['HOME'] = 'linux profile'
        self.assertEqual(
            get_bgmi_path(),
            os.path.normpath(os.path.join('linux profile', '.bgmi')),
        )
        if raw_home is not None:
            os.environ['HOME'] = raw_home

        if old_bgmi_path:
            os.environ['BGMI_PATH'] = old_bgmi_path

    @pytest.mark.skip
    def test_wrong_config_value(self):
        bgmi.config.config_obj.ADMIN_TOKEN = None
        write_default_config()
        with patch('bgmi.config.DOWNLOAD_DELEGATE', 'wrong'):
            self.assertRaises(Exception, write_default_config)

    def test_print_config(self):
        r = config_()
        self.assertEqual(r['status'], ActionStatus.success)

    def test_print_single_config(self):
        r = config_('DANMAKU_API_URL', '233')

        r = config_('DANMAKU_API_URL')
        self.assertEqual(r['status'], ActionStatus.success)
        self.assertTrue(r['message'].startswith('DANMAKU_API_URL'))
        self.assertTrue(r['message'].endswith('233'))

    def test_readonly(self):
        r = config_('CONFIG_FILE_PATH', '/tmp/233')
        self.assertEqual(r['status'], 'error')

    @pytest.mark.skip
    def test_writable(self):
        r = config_('DANMAKU_API_URL', '233')
        self.assertEqual(r['status'], 'success')
        self.assertEqual(bgmi.config.config_obj.DANMAKU_API_URL, '233')

    def test_not_writable(self):
        config_('DAN_API_URL', '233')

    def test_wrong_config_name(self):
        r = config_('WRONG_CONFIG_NAME', '233')
        self.assertEqual(r['status'], 'error')

    # def value_data(self):
    def test_set_wrong_DOWNLOAD_DELEGATE(self):
        delegate = bgmi.config.config_obj.DOWNLOAD_DELEGATE
        r = config_('DOWNLOAD_DELEGATE', 'WRONG_METHOD')
        bgmi.config.read_config()
        self.assertEqual(r['status'], 'error')
        self.assertEqual(bgmi.config.config_obj.DOWNLOAD_DELEGATE, delegate)

    def test_DOWNLOAD_DELEGATE(self):
        config_('DOWNLOAD_DELEGATE', 'aria2-rpc')

    def test_DOWNLOAD_DELEGATE_VALUE(self):
        r = config_('DOWNLOAD_DELEGATE', 'aria2-rpc')
        r = config_('ARIA2_RPC_URL', 'http://some_place/rpc')
        self.assertEqual(r['status'], 'success')
        self.assertEqual(r['message'], 'ARIA2_RPC_URL has been set to http://some_place/rpc')
        self.read()
        self.assertEqual(self.config.get('bgmi', 'ARIA2_RPC_URL'), 'http://some_place/rpc')

    def test_get_DOWNLOAD_DELEGATE_VALUE(self):
        r = config_('ARIA2_RPC_URL')
        self.assertEqual(r['status'], ActionStatus.success)
        self.assertEqual(r['message'], 'ARIA2_RPC_URL=http://127.0.0.1:6800/rpc')


class BadConfigTest(base, unittest.TestCase):
    def test_bad_config_file_missing_options(self):
        # os.remove(CONFIG_FILE_PATH)
        self.read()
        self.config.remove_option('bgmi', 'MAX_PAGE')
        self.write()
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            r = config_('MAX_PAGE')
            self.assertEqual(r['status'], 'error')
            m.assert_any_call()

    @pytest.mark.skip
    def test_bad_config_file_missing_file(self):
        os.remove(CONFIG_FILE_PATH)
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            bgmi.config.read_config()
            m.assert_any_call()

    def test_config_file_not_exist(self):
        os.remove(CONFIG_FILE_PATH)
        with unittest.mock.patch('bgmi.config.write_default_config', unittest.mock.Mock()) as m:
            config_()
            m.assert_any_call()

    def test_read_config_from_env(self):
        os.environ['BGMI_DB_URL'] = 'db_url'
        os.environ['BGMI_ARIA2_RPC_URL'] = 'http://aria2_rpc_url/rpc'
        config = bgmi.config.Config()
        advanced_config = bgmi.config.AdvancedConfig()
        self.assertEqual(advanced_config.DB_URL, 'db_url')
        self.assertEqual(config.ARIA2_RPC_URL, os.environ['BGMI_ARIA2_RPC_URL'])
        del os.environ['BGMI_DB_URL']
        del os.environ['BGMI_ARIA2_RPC_URL']
