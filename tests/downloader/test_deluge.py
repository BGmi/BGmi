from unittest import mock

from bgmi.downloader.deluge import DelugeRPC
from bgmi.website.model import Episode

_token = "deluge"


@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", _token)
def test_use_config():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        DelugeRPC()
        m1.assert_called_with("https://uuu")


@mock.patch("bgmi.downloader.deluge.DelugeRPC._call")
def test_download_magnet(call):
    DelugeRPC(
        download_obj=Episode(name="n", title="t", download="magnet://233"),
        save_path="save_path_1",
    ).download()

    call.assert_called_with(
        "web.add_torrents",
        [
            [
                {
                    "path": "magnet://233",
                    "options": {
                        "add_paused": False,
                        "compact_allocation": False,
                        "move_completed": False,
                        "download_location": "save_path_1",
                        "max_connections": -1,
                        "max_download_speed": -1,
                        "max_upload_slots": -1,
                        "max_upload_speed": -1,
                    },
                }
            ]
        ],
    )


@mock.patch("bgmi.config.DELUGE_RPC_PASSWORD", _token)
@mock.patch("bgmi.downloader.deluge.DelugeRPC._call")
def test_download_torrent(call: mock.Mock):
    call.return_value = {"result": "rr"}

    DelugeRPC(
        download_obj=Episode(name="n", title="t", download="d.torrent"),
        save_path="save_path_1",
    ).download()

    call.assert_has_calls(
        [
            mock.call("auth.login", [_token]),
            mock.call("web.download_torrent_from_url", ["d.torrent"]),
            mock.call(
                "web.add_torrents",
                [
                    [
                        {
                            "path": "rr",
                            "options": {
                                "add_paused": False,
                                "compact_allocation": False,
                                "move_completed": False,
                                "download_location": "save_path_1",
                                "max_connections": -1,
                                "max_download_speed": -1,
                                "max_upload_slots": -1,
                                "max_upload_speed": -1,
                            },
                        }
                    ]
                ],
            ),
        ]
    )
