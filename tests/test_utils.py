# coding=utf-8

import configparser
import json
import os
import os.path
import re
import shutil
import unittest
from types import SimpleNamespace
import unittest.mock
import glob
from unittest.mock import patch, Mock
from bgmi.utils import FRONTEND_NPM_URL, PACKAGE_JSON_URL

import bgmi

from bgmi import utils


class UtilsTest(unittest.TestCase):
    def setUp(self):
        test_dir = './test_dir'
        self.test_dir = test_dir
        # remove test dir if exists
        # if os.path.exists(test_dir) and os.path.isdir(test_dir):
        #     shutil.rmtree(test_dir, )
        if os.path.exists(test_dir):
            if os.path.isdir(test_dir):
                shutil.rmtree(test_dir)
                # os.rmdir(test_dir)
            else:
                os.remove(test_dir, )
        os.mkdir(test_dir)

    def test_download_file(self):
        with patch('bgmi.utils.requests.get') as m:
            m.return_value = 'mock'
            self.assertEqual(utils.download_file('https://hello world'), 'mock')
            m.assert_called_with('https://hello world')

    def test_parse_episode(self):
        with open('tests/data/episode', 'r', encoding='utf8') as f:
            lines = f.readlines()
            lines = [line for line in lines if line]
        for line in lines:
            episode, title = line.split(' ', 1)
            title = title.rstrip()
            episode = int(episode)
            self.assertEqual(episode, utils.parse_episode(title), msg=title)

        return 0

    def test_chinese_to_arabic(self):
        test_case = [
            ['八', 8],
            ['十一', 11],
            ['一百二十三', 123],
            ['一千二百零三', 1203],
            ['一万一千一百零一', 11101],
        ]
        for raw, result in test_case:
            self.assertEqual(utils.chinese_to_arabic(raw), result)

    def test_normalize_path(self):
        self.assertEqual(utils.normalize_path('http://hello? world:/233.qq'), 'http/hello world/233.qq')

    def test_convert_cover_url_to_path(self):
        dir_path, file_path = utils.convert_cover_url_to_path('http://hello? world:/233.qq')
        self.assertEqual(os.path.dirname(file_path), dir_path)
        self.assertTrue(file_path.endswith('http/hello world/233.qq'))

    def test_download_cover(self):
        with patch('bgmi.utils.utils.SAVE_PATH', self.test_dir), patch('bgmi.utils.utils.download_file') as m:
            class Mo:
                def __init__(self, content):
                    self.content = bytes(content, encoding='utf8')

            m.side_effect = lambda x: Mo(x) if x.startswith('https://') or x.startswith('http://') else False

            cover_list = {x: x for x in [
                "https://bangumi.moe/data/images/2014/12/6dv8ukxc0odnwade3pi.jpg",
                "https://bangumi.moe/data/images/2014/12/6dznn2rykghikpgav2k.jpg",
                "https://bangumi.moe/data/images/2014/12/53o20pi40qg4izrj1hj.jpg",
                "https://mikanani.me/Images/Bangumi/201310/91d95f43.jpg",
                "233",
            ]}

            utils.download_cover(list(cover_list.keys()))

            for path in cover_list.keys():
                dir_path, file_path = utils.convert_cover_url_to_path(path)
                if path.startswith('https://') or path.startswith('http://'):
                    with open(file_path, 'rb') as f:
                        self.assertEqual(f.read(), bytes(path, encoding='utf8'))
                else:
                    self.assertFalse(os.path.exists(file_path))

    def test_get_web_admin(self):
        error_response = {
            "error" : "not_found",
            "reason": "document not found"
        }

        with patch('bgmi.utils.utils.requests.get') as m, patch('bgmi.utils.utils.unzip_zipped_file') as unzip:
            request_map = {
                FRONTEND_NPM_URL: Mock(json=Mock(return_value={"version" : '1.2.3',
                                                               'versions':
                                                                   {'1.2.3': {'dist': {'tarball': 'tarball'}}}})),
                PACKAGE_JSON_URL: Mock(json=Mock(return_value={'version': '1.2.3', 'dist': {'tarball': 'tarball'}})),
                'tarball'       : SimpleNamespace(content='tarball content')
            }
            m.side_effect = lambda x: request_map[x]
            utils.get_web_admin('install')
            unzip.assert_called_with('tarball content', {'version': '1.2.3', 'dist': {'tarball': 'tarball'}})

    def test_unzip_zipped_file(self):
        version = {'version': '1.2.3', 'dist': {'tarball': 'tarball'}}
        with open('./tests/data/bgmi-frontend-1.1.4.tgz', 'rb') as f:
            file_content = f.read()
        with patch('bgmi.utils.utils.FRONT_STATIC_PATH', self.test_dir):
            utils.unzip_zipped_file(file_content, {'version': '1.2.3', 'dist': {'tarball': 'tarball'}})
            for file_path in ['index.html', 'static/js/app.js', 'package.json']:
                self.assertTrue(os.path.exists(os.path.join(self.test_dir, file_path)))

    def test_check_update(self):
        # ask for upgrade if old version

        with patch('bgmi.utils.utils.BGMI_PATH', self.test_dir), patch('bgmi.utils.utils.time.time') as time:
            time.return_value = 12345
            version_file = os.path.join(self.test_dir, 'version')
            self.assertFalse(os.path.exists(version_file))
            with patch('bgmi.utils.utils.update') as update:
                utils.check_update()
                update.assert_called_once()
                with open(version_file, 'r') as f:
                    content = f.read()
                    self.assertEqual(content, '12345')
                time.return_value = 12345 + 30 * 30 * 24 * 3600
            with patch('bgmi.utils.utils.update') as update:
                utils.check_update()
                update.assert_called_once()
                with open(version_file, 'r') as f:
                    content = f.read()
                    self.assertEqual(content, str(12345 + 30 * 30 * 24 * 3600))

    def test_update(self):
        with patch('bgmi.utils.utils.FRONT_STATIC_PATH', self.test_dir), patch('bgmi.utils.utils.BGMI_PATH', self.test_dir):
            with patch('bgmi.utils.utils.requests.get') as m, patch('bgmi.utils.utils.get_web_admin')as get_web_admin:
                pypi = 'https://pypi.python.org/pypi/bgmi/json'
                request_map = {
                    FRONTEND_NPM_URL: Mock(json=Mock(return_value={"version" : '1.2.3',
                                                                   'versions': {'1.2.3': {
                                                                       'dist': {'tarball': 'tarball'}}}})),
                    PACKAGE_JSON_URL: Mock(json=Mock(return_value={'version': '1.2.3', 'dist': {'tarball': 'tarball'}})),
                    'tarball'       : SimpleNamespace(content='tarball content'),
                    pypi            : Mock(json=Mock(return_value={'info': {"version": ''}})),
                }

                def mock_get(url, *args, **kwargs):
                    return request_map[url]

                m.side_effect = mock_get

                with open(self.test_dir + '/package.json', 'w', encoding='utf8')as f:
                    json.dump({'version': '1.1.2'}, f)
                utils.update(True)
                get_web_admin.assert_called_once()
