from unittest import mock

import pytest

from bgmi.downloader import DelugeRPC, QBittorrentWebAPI, TransmissionRPC
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.plugin.status import DownloadStatus


@pytest.mark.parametrize(
    "cls", [Aria2DownloadRPC, DelugeRPC, QBittorrentWebAPI, TransmissionRPC]
)
@mock.patch("bgmi.config.ARIA2_RPC_TOKEN", "token:2333")
@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", "deluge")
@mock.patch("bgmi.config.TRANSMISSION_RPC_USERNAME", "tr_username")
@mock.patch("bgmi.config.TRANSMISSION_RPC_PASSWORD", "tr_password")
def test_workflow(torrent_url: str, cls, info_hash: str):
    rpc = cls()
    r = rpc.add_download(url=torrent_url, save_path="/downloads/")
    if r is not None:
        assert r == "cab507494d02ebb1178b38f2e9d7be299c86b862"
    assert rpc.get_status(info_hash) != DownloadStatus.not_found
