import asyncio
import os.path
import sys
import tempfile

import pytest
import requests_cache

from bgmi.config import IS_WINDOWS


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    "session start"
    requests_cache.install_cache(
        os.path.join(tempfile.gettempdir(), "requests.cache"), backend="sqlite",
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
