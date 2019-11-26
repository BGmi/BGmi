import json
import os
import os.path
import shutil
import unittest.mock
from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import Mock, patch

import bgmi
import bgmi.config
from bgmi import utils
from bgmi.lib import constants
from bgmi.utils import utils as inner_utils
from bgmi.utils.utils import FRONTEND_NPM_URL, PACKAGE_JSON_URL

mock_kv_data: Dict[str, Any] = {}


def get_kv_storage():
    return mock_kv_data


@patch('bgmi.lib.db_models.get_kv_storage', get_kv_storage)
class UtilsTest(unittest.TestCase):
    test_dir = './test_dir'

    def setUp(self):
        try:
            os.makedirs(self.test_dir)
        except FileExistsError:
            pass

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except FileNotFoundError:
            pass

    def test_download_file(self):
        with patch('bgmi.utils.utils.requests.get') as m:
            m.return_value = Mock(content=b'mock')
            dir_path, _ = utils.convert_cover_url_to_path('https://hello world')
            try:
                os.makedirs(dir_path)
            except OSError:
                pass
            inner_utils.download_file('https://hello world')
            m.assert_called_with('https://hello world')
            shutil.rmtree(dir_path)
            # os.remove(file_path)

    def test_convert_cover_url_to_path(self):
        dir_path, file_path = utils.convert_cover_url_to_path('http://hello? world:/233.qq')
        self.assertEqual(os.path.dirname(file_path), dir_path)
        self.assertTrue(file_path.endswith('http/hello world/233.qq'))

    def test_download_cover(self):
        with patch('bgmi.config.SAVE_PATH',
                   self.test_dir), patch('bgmi.utils.utils.requests.get') as m:

            class Mo:
                def __init__(self, content):
                    self.content = bytes(content, encoding='utf8')

            m.side_effect = lambda x: Mo(x) if x.startswith('https://'
                                                            ) or x.startswith('http://') else False

            cover_list = {
                x: x for x in [
                    'https://bangumi.moe/data/images/2014/12/6dv8ukxc0odnwade3pi.jpg',
                    'https://bangumi.moe/data/images/2014/12/6dznn2rykghikpgav2k.jpg',
                    'https://bangumi.moe/data/images/2014/12/53o20pi40qg4izrj1hj.jpg',
                    'https://mikanani.me/Images/Bangumi/201310/91d95f43.jpg',
                    '233',
                ]
            }

            utils.download_cover(list(cover_list.keys()))

            for path in cover_list.keys():
                dir_path, file_path = utils.convert_cover_url_to_path(path)
                if path.startswith('https://') or path.startswith('http://'):
                    with open(file_path, 'rb') as f:
                        self.assertEqual(f.read(), bytes(path, encoding='utf8'))
                else:
                    self.assertFalse(os.path.exists(file_path))

    def test_get_web_admin(self):
        with patch('bgmi.utils.utils.requests.get'
                   ) as m, patch('bgmi.utils.utils.unzip_zipped_file') as unzip:
            request_map = {
                FRONTEND_NPM_URL: Mock(
                    json=Mock(
                        return_value={
                            'version': '1.2.3',
                            'versions': {'1.2.3': {'dist': {'tarball': 'tarball'}}}
                        }
                    )
                ), PACKAGE_JSON_URL: Mock(
                    json=Mock(return_value={'version': '1.2.3', 'dist': {'tarball': 'tarball'}})
                ), 'tarball': SimpleNamespace(content='tarball content')
            }
            m.side_effect = lambda x: request_map[x]
            utils.get_web_admin()
            unzip.assert_called_with(
                'tarball content', {'version': '1.2.3', 'dist': {'tarball': 'tarball'}}
            )

    def test_unzip_zipped_file(self):
        with open('./tests/data/bgmi-frontend-1.1.4.tgz', 'rb') as f:
            file_content = f.read()
        with patch('bgmi.config.FRONT_STATIC_PATH', self.test_dir):
            inner_utils.unzip_zipped_file(
                file_content, {'version': '1.2.3', 'dist': {'tarball': 'tarball'}}
            )
            for file_path in ['index.html', 'static/js/app.js', 'package.json']:
                self.assertTrue(os.path.exists(os.path.join(self.test_dir, file_path)))

    def test_check_update(self):
        # ask for upgrade if old version

        with patch('bgmi.utils.utils.time.time') as time:
            time.return_value = 12345
            with patch('bgmi.utils.utils.update') as update:
                get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = time.return_value
                utils.check_update()
                update.assert_not_called()
                self.assertEqual(get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME), 12345)

            time.return_value = 12345 + 30 * 30 * 24 * 3600
            with patch('bgmi.utils.utils.update') as update:
                get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = 12345
                utils.check_update()
                update.assert_called_once_with(True)
                self.assertEqual(
                    get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME),
                    12345 + 30 * 30 * 24 * 3600
                )

    def test_update(self):
        with patch('bgmi.utils.utils.requests.get') as m, \
                patch('bgmi.utils.utils.get_web_admin', Mock()) as get_web_admin:
            pypi = 'https://pypi.python.org/pypi/bgmi/json'
            request_map = {
                FRONTEND_NPM_URL: Mock(
                    json=Mock(
                        return_value={
                            'version': '1.2.3',
                            'versions': {'1.2.3': {'dist': {'tarball': 'tarball'}}}
                        }
                    )
                ),
                PACKAGE_JSON_URL: Mock(
                    json=Mock(return_value={'version': '1.2.3', 'dist': {'tarball': 'tarball'}})
                ),
                'tarball': SimpleNamespace(content='tarball content'),
                pypi: Mock(json=Mock(return_value={'info': {'version': ''}})),
            }

            def mock_get(url, *args, **kwargs):
                return request_map[url]

            m.side_effect = mock_get
            if not os.path.exists(bgmi.config.FRONT_STATIC_PATH):
                os.makedirs(bgmi.config.FRONT_STATIC_PATH)
            with open(bgmi.config.FRONT_STATIC_PATH + '/package.json', 'w+', encoding='utf8') as f:
                json.dump({'version': '1.1.2'}, f)
            inner_utils.update(True)
            get_web_admin.assert_any_call()
