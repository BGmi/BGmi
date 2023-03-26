from unittest import mock

from bgmi.downloader.aria2_rpc import Aria2DownloadRPC

_token = "token:2333"


@mock.patch("bgmi.config.cfg.aria2.rpc_url", "https://uuu")
@mock.patch("bgmi.config.cfg.aria2.rpc_token", "token:t")
def test_use_config():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        m1.return_value.aria2.getVersion.return_value = {"version": "1.19.1"}
        Aria2DownloadRPC()
        m1.assert_has_calls(
            [
                mock.call("https://uuu"),
                mock.call("https://uuu"),
                mock.call().aria2.getVersion("token:t"),
            ]
        )
