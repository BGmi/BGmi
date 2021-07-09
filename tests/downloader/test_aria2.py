from unittest import mock

from bgmi.downloader.aria2_rpc import Aria2DownloadRPC

_token = "token:2334"


@mock.patch("bgmi.config.ARIA2_RPC_URL", "https://uuu")
def test_use_config():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        m1.return_value.aria2.getVersion.return_value = {"version": "1.19.1"}
        Aria2DownloadRPC()
        m1.assert_called_once_with("https://uuu")
