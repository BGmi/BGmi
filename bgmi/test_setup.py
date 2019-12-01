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

    def test_get_web_admin(self):
        with patch('requests.get') as m, patch('bgmi.utils.unzip_zipped_file') as unzip:
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
            bgmi.setup.get_web_admin()
            unzip.assert_called_with(
                'tarball content', {'version': '1.2.3', 'dist': {'tarball': 'tarball'}}
            )
