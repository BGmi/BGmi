from unittest import mock

from bgmi.downloader.transmission import TransmissionRPC
from bgmi.website.model import Episode


@mock.patch("transmission_rpc.Client")
def test_download(client_mock, clean_bgmi):
    add_torrent = mock.Mock()
    client_mock.return_value.add_torrent = add_torrent

    TransmissionRPC(
        download_obj=Episode(name="n", title="t", download="d"),
        save_path="save_path",
    ).download()

    client_mock.assert_called_once()
    add_torrent.assert_called_with("d", download_dir="save_path")
