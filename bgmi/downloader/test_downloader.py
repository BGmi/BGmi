import urllib.parse
from typing import Type

import mock
import pytest

from bgmi import config
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.base import AuthError, ConnectError
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmissionRpc import BaseDownloadService, TransmissionRPC

# @pytest.mark.parametrize('rpc_name', DOWNLOAD_DELEGATE_MAP.keys())
# def test_get_all_download_class(rpc_name):
#     assert isinstance(get_download_class(rpc_name), BaseDownloadService)

# @pytest.mark.parametrize('test_class', [Aria2DownloadRPC, DelugeRPC, TransmissionRPC])
# def test_download(test_class: Type[BaseDownloadService]):
#     test_class.require()
#     origin_require = test_class.require
#     mock_require = mock.Mock()
#     test_class.require = mock_require
#     try:
#         downloader_instance = test_class()
#     except:
#         pass
#     assert mock_require.called_once()
TEST_DOWNLOADER = [
    Aria2DownloadRPC,
    DelugeRPC,
    TransmissionRPC,
]


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_raise_connect_error(test_class: Type[BaseDownloadService], set_wrong_addr):
    with pytest.raises(ConnectError):
        test_class()


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_raise_auth_error(test_class: Type[BaseDownloadService], set_wrong_auth):
    with pytest.raises(AuthError):
        test_class()


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_magnet(test_class: Type[BaseDownloadService]):
    downloader_instance = test_class()
    downloader_instance.download(
        torrent='magnet:?xt=urn:btih:ff9a3613357e955fc7090eeb1cc7808ef51c9521',
        save_path='/downloads',
    )


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_torrent_file_url(test_class: Type[BaseDownloadService]):
    TransmissionRPC().client.set_session()
    downloader_instance = test_class()
    downloader_instance.download(
        torrent='https://mikanani.me/Download/20190706/'
        'ff9a3613357e955fc7090eeb1cc7808ef51c9521.torrent',
        save_path='/downloads',
    )


@pytest.fixture()
def set_wrong_auth(test_class: Type[BaseDownloadService]):
    if issubclass(test_class, Aria2DownloadRPC):
        with mock.patch('bgmi.config.ARIA2_RPC_TOKEN', 'wrong auth'):
            yield
    elif issubclass(test_class, DelugeRPC):
        with mock.patch('bgmi.config.DELUGE_RPC_PASSWORD', 'wrong auth'):
            yield
    elif issubclass(test_class, TransmissionRPC):
        origin_url = config.TRANSMISSION_RPC_URL
        url = urllib.parse.urlparse(origin_url)  # type: urllib.parse.ParseResult
        with mock.patch(
            'bgmi.config.TRANSMISSION_RPC_URL',
            f'{url.scheme}://{url.hostname}:{url.port}{url.path}'
        ):
            yield
    else:
        yield


@pytest.fixture()
def set_wrong_addr(test_class: Type[BaseDownloadService]):
    if issubclass(test_class, Aria2DownloadRPC):
        with mock.patch('bgmi.config.ARIA2_RPC_URL', 'http://127.0.0.1:6715/rpc'):
            yield
    elif issubclass(test_class, DelugeRPC):
        with mock.patch('bgmi.config.DELUGE_RPC_URL', 'http://127.0.0.1:6715/json'):
            yield
    elif issubclass(test_class, TransmissionRPC):
        with mock.patch(
            'bgmi.config.TRANSMISSION_RPC_URL', 'http://127.0.0.1:6715/transmission/rpc'
        ):
            yield
    else:
        yield
