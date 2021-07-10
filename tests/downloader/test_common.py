import time
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
    # aria2 didn't take info_hash as torrent id
    time.sleep(1)
    now = time.time()
    while time.time() - now < 10:
        # wait for 10 second
        status = rpc.get_status(r or info_hash)
        if status == DownloadStatus.downloading:
            return
        time.sleep(0.5)
    pytest.fail("can't find download task with timeout 10s")
