import unittest

import bgmi.config as bgmi_config
from bgmi.lib.controllers import cfg


class ConfigTest(unittest.TestCase):
    def test_print_config(self):
        r = cfg()
        assert r["status"] == "info"

    def test_print_single_config(self):
        r = cfg("DANMAKU_API_URL", "233")

        r = cfg("DANMAKU_API_URL")
        assert r["status"] == "info"
        assert r["message"].startswith("DANMAKU_API_URL")
        assert r["message"].endswith("233")

    def test_readonly(self):
        r = cfg("DB_PATH", "/tmp/233")
        assert r["status"] == "error"

    def test_writable(self):
        r = cfg("DANMAKU_API_URL", "233")
        assert r["status"] == "success"
        from bgmi.config import DANMAKU_API_URL

        assert DANMAKU_API_URL == "233"

    def test_source(self):
        r = cfg("DATA_SOURCE", "233")
        assert r["status"] == "error"

    def test_wrong_config_name(self):
        r = cfg("WRONG_CONFIG_NAME", "233")
        assert r["status"] == "error"

    def test_DOWNLOAD_DELEGATE(self):
        cfg("DOWNLOAD_DELEGATE", "aria2-rpc")
        cfg("DOWNLOAD_DELEGATE", "rr!")
        cfg("WGET_PATH", "some_place")

    @classmethod
    def setUpClass(cls):
        import os

        from bgmi.config import CONFIG_FILE_PATH

        os.remove(CONFIG_FILE_PATH)
        bgmi_config.write_default_config()
        print(os.path.exists(CONFIG_FILE_PATH))
