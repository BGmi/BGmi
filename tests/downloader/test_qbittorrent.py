from unittest import mock

from bgmi.config import QBITTORRENT_CATEGORY
from bgmi.downloader.qbittorrent import QBittorrentWebAPI
from bgmi.website.model import Episode


@mock.patch("qbittorrentapi.Client")
def test_download(client_mock):
    torrents_add = mock.Mock()
    client_mock.return_value.torrents_add = torrents_add

    QBittorrentWebAPI(
        download_obj=Episode(name="n", title="t", download="d"),
        save_path="save_path",
    ).download()

    client_mock.assert_called_once()
    torrents_add.assert_called_with(
        urls="d",
        category=QBITTORRENT_CATEGORY,
        save_path="save_path",
        is_paused=False,
        use_auto_torrent_management=False,
    )
