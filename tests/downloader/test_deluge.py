from unittest import mock

from bgmi.downloader.deluge import DelugeRPC

_token = "ttttt"


@mock.patch("bgmi.config.cfg.deluge.rpc_password", _token)
@mock.patch.object(DelugeRPC, "_call")
def test_use_config(mock_call: mock.Mock):
    DelugeRPC()
    mock_call.assert_called_once_with("auth.login", [_token])
