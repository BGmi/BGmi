import os
from unittest import mock

import pytest

from bgmi.config import MAX_PAGE, SAVE_PATH
from bgmi.lib.controllers import update
from bgmi.lib.models import Bangumi, Followed
from bgmi.main import main
from bgmi.website.model import Episode


@pytest.mark.usefixtures("_clean_bgmi")
def test_search_download(mock_download_driver: mock.Mock):
    mock_website = mock.Mock()
    mock_website.search_by_keyword = mock.Mock(
        return_value=[
            Episode(
                episode=3,
                download="magnet:mm",
                title="m-title 720p",
                name="海贼王",
            ),
            Episode(
                episode=4,
                download="magnet:4",
                title="m-title 1080p",
                name="海贼王",
            ),
        ]
    )
    with mock.patch("bgmi.lib.controllers.website", mock_website):
        main("search 海贼王 --download".split())

    mock_website.search_by_keyword.assert_called_once_with("海贼王", count=MAX_PAGE)

    mock_download_driver.add_download.assert_has_calls(
        [
            mock.call(url="magnet:mm", save_path=os.path.join(SAVE_PATH, "海贼王", "3")),
            mock.call(url="magnet:4", save_path=os.path.join(SAVE_PATH, "海贼王", "4")),
        ]
    )


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_download(mock_download_driver: mock.Mock):
    """TODO: mock HTTP requests in this test"""
    bangumi_name = "hello world"
    mock_website = mock.Mock()
    mock_website.get_maximum_episode = mock.Mock(
        return_value=(
            4,
            [
                Episode(
                    episode=3,
                    download="magnet:mm",
                    title="m-title 720p",
                    name=bangumi_name,
                ),
                Episode(
                    episode=4,
                    download="magnet:4",
                    title="m-title 1080p",
                    name=bangumi_name,
                ),
            ],
        )
    )

    Bangumi(name=bangumi_name, subtitle_group="", keyword=bangumi_name, cover="").save()
    Followed(bangumi_name=bangumi_name, episode=2).save()

    with mock.patch("bgmi.lib.controllers.website", mock_website):
        update([], download=True, not_ignore=False)

    mock_download_driver.add_download.assert_has_calls(
        [
            mock.call(
                url="magnet:mm", save_path=os.path.join(SAVE_PATH, bangumi_name, "3")
            ),
            mock.call(
                url="magnet:4", save_path=os.path.join(SAVE_PATH, bangumi_name, "4")
            ),
        ]
    )


def test_search_with_filter(mock_download_driver: mock.Mock):
    mock_website = mock.Mock()
    mock_website.search_by_keyword = mock.Mock(
        return_value=[
            Episode(
                episode=3,
                download="magnet:mm",
                title="m-title 720p",
                name="海贼王",
            ),
            Episode(
                episode=4,
                download="magnet:4",
                title="m-title 1080p",
                name="海贼王",
            ),
        ]
    )

    with mock.patch("bgmi.lib.controllers.website", mock_website):
        main("search 海贼王 --download --regex .*720.*".split())

    mock_website.search_by_keyword.assert_called_once_with("海贼王", count=MAX_PAGE)

    mock_download_driver.add_download.assert_called_once_with(
        url="magnet:mm", save_path=os.path.join(SAVE_PATH, "海贼王", "3")
    )
