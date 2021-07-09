from unittest import mock

from bgmi.downloader.aria2_rpc import Aria2DownloadRPC

_token = "token:2333"


@mock.patch("bgmi.config.ARIA2_RPC_URL", "https://uuu")
def test_use_config():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        m1.return_value.aria2.getVersion.return_value = {"version": "1.19.1"}
        Aria2DownloadRPC()
        m1.assert_has_calls([mock.call("https://uuu")])


@mock.patch("bgmi.config.ARIA2_RPC_TOKEN", _token)
def test_add_download(torrent_url: str):
    Aria2DownloadRPC().add_download(url=torrent_url, save_path="/downloads/")
