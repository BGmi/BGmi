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
import bgmi.lib.update
import bgmi.setup
from bgmi.config import FRONTEND_NPM_URL, PACKAGE_JSON_URL
from bgmi.lib import constants

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

    def test_check_update(self):
        # ask for upgrade if old version

        with patch('time.time') as time:
            time.return_value = 12345
            with patch('bgmi.lib.update.update') as update:
                get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = time.return_value
                bgmi.lib.update.check_update()
                update.assert_not_called()
                self.assertEqual(get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME), 12345)

            time.return_value = 12345 + 30 * 30 * 24 * 3600
            with patch('bgmi.lib.update.update') as update:
                get_kv_storage()[constants.kv.LAST_CHECK_UPDATE_TIME] = 12345
                bgmi.lib.update.check_update()
                update.assert_called_once_with(True)
                self.assertEqual(
                    get_kv_storage().get(constants.kv.LAST_CHECK_UPDATE_TIME),
                    12345 + 30 * 30 * 24 * 3600
                )

    def test_update(self):
        with patch('requests.get') as m, patch(
            'bgmi.lib.update.get_web_admin', Mock()
        ) as get_web_admin:
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
            bgmi.lib.update.update(True)
            get_web_admin.assert_any_call()
