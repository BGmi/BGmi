from unittest import mock

from bgmi.downloader.deluge import DelugeRPC
from bgmi.plugin.status import DownloadStatus

_token = "deluge"


@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", _token)
@mock.patch.object(DelugeRPC, "_call")
def test_use_config(mock_call: mock.Mock):
    DelugeRPC()
    mock_call.assert_called_once_with("auth.login", [_token])


@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", _token)
def test_workflow(torrent_url: str):
    rpc = DelugeRPC()
    info_hash = rpc.add_download(url=torrent_url, save_path="/downloads/")
    assert rpc.get_status(info_hash) == DownloadStatus.downloading
