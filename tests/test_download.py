import os
from unittest import mock

import pytest

from bgmi.config import cfg
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.controllers import update
from bgmi.lib.download import add_tracker
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

    mock_website.search_by_keyword.assert_called_once_with("海贼王", count=None)

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

    Bangumi(id=name, name=name).save()

    Followed(bangumi_name=name, episodes={1, 2}).save()

    assert Followed.get(Followed.bangumi_name == name).episodes == {1, 2}

    with mock.patch("bgmi.lib.controllers.website", mock_website):
        update([name], download=True, not_ignore=False)

    mock_download_driver.add_download.assert_has_calls(
        [
            mock.call(
                url="http://example.com/Bangumi/1/2.torrent", save_path=os.path.join(cfg.save_path, "TEST_BANGUMI", "2")
            ),
            mock.call(
                url=add_tracker("magnet:?xt=urn:btih:233"), save_path=os.path.join(cfg.save_path, "TEST_BANGUMI", "3")
            ),
            mock.call(url=add_tracker("magnet:mm"), save_path=os.path.join(cfg.save_path, name, "3")),
            mock.call(url=add_tracker("magnet:4"), save_path=os.path.join(cfg.save_path, name, "4")),
        ]
    )


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_weekday_download(mock_download_driver: mock.Mock):
    with Session.begin() as session:
        session.query(Download).delete()
        assert session.query(Download).count() == 0

    sun_name = "Update at Sun"
    mon_name = "Update at mon"
    Bangumi(id=sun_name, name=sun_name, update_day=BANGUMI_UPDATE_TIME[0]).save()
    Bangumi(id=mon_name, name=mon_name, update_day=BANGUMI_UPDATE_TIME[1]).save()

    mock_website = mock.Mock()

    def side_effect(*args, **kwargs):
        data = {
            sun_name: [Episode(episode=3, download="magnet:sun", title="t 720p", name=sun_name)],
            mon_name: [Episode(episode=3, download="magnet:mon", title="t 1080p", name=mon_name)],
        }
        return data[kwargs["bangumi"].name]

    mock_website.get_maximum_episode = mock.Mock(side_effect=side_effect)

    Followed(bangumi_name=sun_name, episodes={1, 2}).save()
    Followed(bangumi_name=mon_name, episodes={1, 2}).save()

    assert Followed.get(Followed.bangumi_name == sun_name).episodes == {1, 2}
    assert Followed.get(Followed.bangumi_name == mon_name).episodes == {1, 2}

    # Update Sunday bangumis, Monday bangumis(include scripts) should not be updated
    with mock.patch("bgmi.lib.controllers.website", mock_website):
        update(names=[], download=True, not_ignore=False, update_days=[BANGUMI_UPDATE_TIME[0]])

    mock_download_driver.add_download.assert_called_once_with(
        url=add_tracker("magnet:sun"), save_path=os.path.join(cfg.save_path, sun_name, "3")
    )

    assert Followed.get(Followed.bangumi_name == sun_name).episodes == {1, 2, 3}
    assert Followed.get(Followed.bangumi_name == mon_name).episodes == {1, 2}

    # Update Monday bangumis, they can be updated this turn
    with mock.patch("bgmi.lib.controllers.website", mock_website):
        update(names=[], download=True, not_ignore=False, update_days=[BANGUMI_UPDATE_TIME[1]])

    mock_download_driver.add_download.assert_has_calls(
        [
            mock.call(
                url="http://example.com/Bangumi/1/2.torrent", save_path=os.path.join(cfg.save_path, "TEST_BANGUMI", "2")
            ),
            mock.call(
                url=add_tracker("magnet:?xt=urn:btih:233"), save_path=os.path.join(cfg.save_path, "TEST_BANGUMI", "3")
            ),
            mock.call(url=add_tracker("magnet:mon"), save_path=os.path.join(cfg.save_path, mon_name, "3")),
        ]
    )

    assert Followed.get(Followed.bangumi_name == sun_name).episodes == {1, 2, 3}
    assert Followed.get(Followed.bangumi_name == mon_name).episodes == {1, 2, 3}


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

    mock_website.search_by_keyword.assert_called_once_with("海贼王", count=None)

    mock_download_driver.add_download.assert_called_once_with(
        url="magnet:mm", save_path=os.path.join(cfg.save_path, "海贼王", "3")
    )
