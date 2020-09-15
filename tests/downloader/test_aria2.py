from unittest import mock

from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.website.model import Episode

_token = "token:2334"


@mock.patch("bgmi.config.ARIA2_RPC_TOKEN", _token)
def test_download():
    # with mock.patch("bgmi.downloader.aria2_rpc.PatchedServerProxy") as m1:
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        addUri = mock.Mock()
        m1.return_value.aria2.addUri = addUri
        m1.return_value.aria2.getVersion.return_value = {"version": "1.19.1"}

        Aria2DownloadRPC(
            download_obj=Episode(name="n", title="t", download="d"),
            save_path="save_path",
        ).download()

        # m1.assert_called_once()
        addUri.assert_called_with(_token, ["d"], {"dir": "save_path"})


@mock.patch("bgmi.config.ARIA2_RPC_TOKEN", _token)
def test_download_status():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        aria2 = m1.return_value.aria2

        for method in ["tellStopped", "tellWaiting", "tellActive"]:
            getattr(aria2, method).return_value = [{"dir": "", "files": []}]
        aria2.getVersion.return_value = {"version": "1.19.1"}

        Aria2DownloadRPC.download_status()

        for method in ["tellStopped", "tellWaiting"]:
            getattr(m1.return_value.aria2, method).assert_called_with(_token, 0, 1000)
        aria2.tellActive.assert_called_with(_token)


@mock.patch("bgmi.config.ARIA2_RPC_TOKEN", _token)
def test_old_version_download_status():
    with mock.patch("xmlrpc.client.ServerProxy") as m1:
        aria2 = m1.return_value.aria2
        for method in ["tellStopped", "tellWaiting", "tellActive"]:
            getattr(aria2, method).return_value = [{"dir": "", "files": []}]
        m1.return_value.aria2.getVersion.return_value = {"version": "1.17.1"}

        Aria2DownloadRPC.download_status()

        for method in ["tellStopped", "tellWaiting"]:
            getattr(aria2, method).assert_called_with(0, 1000)
        aria2.tellActive.assert_called_with()
