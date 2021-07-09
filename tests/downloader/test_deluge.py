from unittest import mock

from bgmi.downloader.deluge import DelugeRPC

_token = "deluge"


@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", _token)
def test_use_config():
    DelugeRPC()
