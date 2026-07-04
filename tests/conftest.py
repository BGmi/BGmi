import os.path
import shutil
import tempfile
from unittest import mock

import pytest
import requests_cache
import urllib3

from bgmi.config import cfg
from bgmi.lib.table import (
    Bangumi,
    Followed,
    Session,
    Scripts,
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
def _calendar_cache():
    """Fetch calendar once per source, shared across fixtures."""
    import random

    from bgmi.lib.fetch import DATA_SOURCE_MAP

    cache = {}
    for source_name, source_cls in DATA_SOURCE_MAP.items():
        bangumi_list = source_cls().fetch_bangumi_calendar()
        assert bangumi_list, f"Calendar fetch returned empty for {source_name}"
        random.shuffle(bangumi_list)
        cache[source_name] = bangumi_list
    return cache


@pytest.fixture()
def data_source_bangumi_name(_calendar_cache):
    return {source: [b.name for b in bl[:5]] for source, bl in _calendar_cache.items()}


@pytest.fixture()
def data_source_subtitle_name(_calendar_cache):
    from bgmi.lib.fetch import DATA_SOURCE_MAP

    result = {}
    for source_name, bangumi_list in _calendar_cache.items():
        pairs = []
        for b in bangumi_list:
            if b.subtitle_group:
                pairs.append((b.name, b.subtitle_group[0].name))
                if len(pairs) >= 5:
                    break
        if not pairs:
            w = DATA_SOURCE_MAP[source_name]()
            for b in bangumi_list[:3]:
                info = w.fetch_single_bangumi(b.id)
                if info and info.subtitle_group:
                    pairs.append((b.name, info.subtitle_group[0].name))
                    if len(pairs) >= 5:
                        break
        if pairs:
            result[source_name] = pairs
    return result


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
    return [pair[1] for pair in data_source_subtitle_name["bangumi_moe"][:1]]


@pytest.fixture()
def mock_download_driver():
    mock_downloader = mock.Mock()
    mock_downloader.add_download.return_value = "mock-task-id"
    with mock.patch("bgmi.lib.download.get_download_driver", mock.Mock(return_value=mock_downloader)):
        yield mock_downloader


bangumi_name_1 = "名侦探柯南"
bangumi_name_2 = "海贼王"


@pytest.fixture()
def _ensure_data():
    with Session.begin() as tx:
        tx.query(Bangumi).delete()
        tx.query(Followed).delete()
        tx.query(Scripts).delete()
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
        tx.add(Followed(bangumi_name=bangumi_name_1, episodes={1, 2}))
