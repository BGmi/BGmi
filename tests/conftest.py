import asyncio
import os.path
import shutil
import tempfile
from unittest import mock

import pytest
import requests_cache
import urllib3

from bgmi.config import IS_WINDOWS, SCRIPT_PATH
from bgmi.lib.models import recreate_source_relatively_table


def pytest_addoption(parser):
    parser.addoption("--cache-requests", action="store_true")


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    "session start"
    if session.cfg.getoption("--cache-requests"):
        requests_cache.install_cache(
            os.path.join(tempfile.gettempdir(), "requests.cache"),
            backend="sqlite",
            allowable_methods=("GET", "POST"),
        )
    ensure_example_script()
    urllib3.disable_warnings()
    if IS_WINDOWS:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def ensure_example_script():
    test_script = "script_example.py"
    p = os.listdir(SCRIPT_PATH)
    if test_script not in p:
        print("copy script_example.py to SCRIPT_PATH")
        shutil.copy(
            os.path.join(os.path.dirname(__file__), "..", test_script),
            os.path.join(SCRIPT_PATH, test_script),
        )


@pytest.fixture()
def data_source_bangumi_name():
    return {
        "bangumi_moe": ["名侦探柯南", "妖精的尾巴"],
        "mikan_project": ["名侦探柯南", "海贼王"],
        "dmhy": ["名偵探柯南", "海賊王"],
    }


@pytest.fixture()
def data_source_subtitle_name():
    return {
        "bangumi_moe": ["LoliHouse"],
        "mikan_project": ["LoliHouse"],
    }


@pytest.fixture()
def _clean_bgmi():
    recreate_source_relatively_table()
    yield
    recreate_source_relatively_table()


@pytest.fixture()
def bangumi_names(data_source_bangumi_name):
    return data_source_bangumi_name["bangumi_moe"]


@pytest.fixture()
def bangumi_subtitles(data_source_subtitle_name):
    return data_source_subtitle_name["bangumi_moe"]


@pytest.fixture()
def mock_download_driver():
    mock_downloader = mock.Mock()
    with mock.patch("bgmi.lib.download.get_download_driver", mock.Mock(return_value=mock_downloader)):
        yield mock_downloader
