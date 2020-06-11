import asyncio
import os.path
import sys
import tempfile

import pytest
import requests_cache

from bgmi.config import IS_WINDOWS
from bgmi.lib.models import recreate_source_relatively_table


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

    if IS_WINDOWS:
        if sys.version_info[1] >= 8:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture()
def data_source_bangumi_name():
    return {
        "bangumi_moe": ["名侦探柯南", "海贼王", "黑色五叶草"],
        "mikan_project": ["名侦探柯南", "海贼王"],
        "dmhy": ["名偵探柯南", "海賊王"],
    }


@pytest.fixture()
def clean_bgmi():
    recreate_source_relatively_table()
    yield
    recreate_source_relatively_table()
