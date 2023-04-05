import os
from unittest import mock

import pytest

from bgmi.config import cfg
from bgmi.lib.controllers import update
from bgmi.lib.table import Bangumi, Download, Followed, Session
from bgmi.main import main_for_test
from bgmi.website.model import Episode


@pytest.mark.usefixtures("_clean_bgmi")
def test_search_download(mock_download_driver: mock.Mock):
    mock_website = mock.Mock()
    mock_website.search_by_keyword = mock.Mock(
        return_value=[
            Episode(episode=3, download="magnet:mm", title="t 720p", name="海贼王"),
            Episode(episode=4, download="magnet:4", title="t 1080p", name="海贼王"),
        ]
    )
    with mock.patch("bgmi.lib.controllers.website", mock_website):
        main_for_test("search 海贼王 --download".split())

    mock_website.search_by_keyword.assert_called_once_with("海贼王", count=cfg.max_path)

    mock_download_driver.add_download.assert_has_calls(
        [
            mock.call(url="magnet:mm", save_path=os.path.join(cfg.save_path, "海贼王", "3")),
            mock.call(url="magnet:4", save_path=os.path.join(cfg.save_path, "海贼王", "4")),
        ]
    )


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_download(mock_download_driver: mock.Mock):
    with Session.begin() as session:
        session.query(Download).delete()
        assert session.query(Download).count() == 0

    name = "hello world"
    mock_website = mock.Mock()
    mock_website.get_maximum_episode = mock.Mock(
        return_value=[
            Episode(episode=3, download="magnet:mm", title="t 720p", name=name),
            Episode(episode=4, download="magnet:4", title="t 1080p", name=name),
        ],
    )

    Bangumi(name=name, subtitle_group="", keyword=name, cover="").save()

    Followed(bangumi_name=name, episode=2).save()

    assert Followed.get(Followed.bangumi_name == name).episode == 2

    with mock.patch("bgmi.lib.controllers.website", mock_website):
        update([name], download=True, not_ignore=False)

    mock_download_driver.add_download.assert_has_calls(
        [
            mock.call(
                url="http://example.com/Bangumi/1/2.torrent", save_path=os.path.join(cfg.save_path, "TEST_BANGUMI", "2")
            ),
            mock.call(url="magnet:?xt=urn:btih:233", save_path=os.path.join(cfg.save_path, "TEST_BANGUMI", "3")),
            mock.call(url="magnet:mm", save_path=os.path.join(cfg.save_path, name, "3")),
            mock.call(url="magnet:4", save_path=os.path.join(cfg.save_path, name, "4")),
        ]
    )


def test_search_with_filter(mock_download_driver: mock.Mock):
    mock_website = mock.Mock()
    mock_website.search_by_keyword = mock.Mock(
        return_value=[
            Episode(episode=3, download="magnet:mm", title="t 720p", name="海贼王"),
            Episode(episode=4, download="magnet:4", title="t 1080p", name="海贼王"),
        ]
    )

    with mock.patch("bgmi.lib.controllers.website", mock_website):
        main_for_test("search 海贼王 --download --regex-filter .*720.*".split())

    mock_website.search_by_keyword.assert_called_once_with("海贼王", count=cfg.max_path)

    mock_download_driver.add_download.assert_called_once_with(
        url="magnet:mm", save_path=os.path.join(cfg.save_path, "海贼王", "3")
    )
