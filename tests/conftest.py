import asyncio
import os.path
import shutil
import tempfile
from unittest import mock

import pytest
import requests_cache
import urllib3

from bgmi.config import IS_WINDOWS, cfg
from bgmi.lib.table import (
    Bangumi,
    Followed,
    Session,
    Subtitle,
    recreate_scripts_table,
    recreate_source_relatively_table,
)


def pytest_addoption(parser):
    parser.addoption("--cache-requests", action="store_true")


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    "session start"
    if session.config.getoption("--cache-requests"):
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
    p = os.listdir(cfg.script_path)
    if test_script not in p:
        print("copy script_example.py to SCRIPT_PATH")
        shutil.copy(
            os.path.join(os.path.dirname(__file__), test_script),
            os.path.join(cfg.script_path, test_script),
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
    recreate_scripts_table()
    recreate_source_relatively_table()
    yield
    recreate_source_relatively_table()
    recreate_scripts_table()


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


bangumi_name_1 = "名侦探柯南"
bangumi_name_2 = "海贼王"


@pytest.fixture()
def ensure_data():
    with Session.begin() as tx:
        tx.query(Bangumi).delete()
        tx.query(Followed).delete()
        tx.query(Subtitle).delete()
        tx.add(Bangumi(name=bangumi_name_1, id="1", subtitle_group=["id1", "id2"], cover="hello"))
        tx.add(Bangumi(name=bangumi_name_2, id="2"))
        tx.add_all(
            [
                Subtitle(id="id1", name="sg1"),
                Subtitle(id="id2", name="sg2"),
                Subtitle(id="id3", name="sg3"),
            ]
        )
        tx.add(Followed(bangumi_name=bangumi_name_1, episode=2))
