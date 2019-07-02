import pytest

from bgmi.config import DOWNLOAD_DELEGATE_MAP
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmissionRpc import BaseDownloadService, TransmissionRPC
from bgmi.lib.download import get_download_class


@pytest.mark.parametrize('rpc_name', DOWNLOAD_DELEGATE_MAP.keys())
def test_get_all_download_class(rpc_name):
    assert issubclass(get_download_class(rpc_name), BaseDownloadService)


@pytest.mark.parametrize('test_class', [Aria2DownloadRPC, DelugeRPC, TransmissionRPC])
def test_download(test_class: BaseDownloadService):
    test_class.install()
    # test_class.download()
