from unittest import mock

from bgmi.downloader.deluge import DelugeRPC

_token = "deluge"


@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", _token)
def test_use_config():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        DelugeRPC()
        m1.assert_called_with("https://uuu")
