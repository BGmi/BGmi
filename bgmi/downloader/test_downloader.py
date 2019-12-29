from typing import Type

import mock
import pytest

from bgmi import config
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.base import AuthError, ConnectError
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmissionRpc import BaseDownloadService, TransmissionRPC
from bgmi.models import Config

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
        test_class(config.config_obj)


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_raise_auth_error(test_class: Type[BaseDownloadService], set_wrong_auth):
    with pytest.raises(AuthError):
        test_class(set_wrong_auth)


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_magnet(test_class: Type[BaseDownloadService]):
    downloader_instance = test_class(config.config_obj)
    downloader_instance.download(
        torrent='magnet:?xt=urn:btih:d3e841c79c1d7c0ec60df0c414356ac0d2833f22',
        save_path='/downloads',
    )


@pytest.mark.parametrize('test_class', TEST_DOWNLOADER)
def test_torrent_file_url(test_class: Type[BaseDownloadService]):
    downloader_instance = test_class(config.config_obj)
    downloader_instance.download(
        torrent='https://mikanani.me/Download/20190706/'
        'ff9a3613357e955fc7090eeb1cc7808ef51c9521.torrent',
        save_path='/downloads',
    )


@pytest.fixture()
def set_wrong_auth(test_class: Type[BaseDownloadService]):
    if issubclass(test_class, Aria2DownloadRPC):
        yield Config(ARIA2_RPC_TOKEN='token:wrong auth')
    elif issubclass(test_class, DelugeRPC):
        yield Config(DELUGE_RPC_PASSWORD='wrong auth')
    elif issubclass(test_class, TransmissionRPC):
        url = config.config_obj.TRANSMISSION_RPC_URL
        # url: urllib.parse.ParseResult = urllib.parse.urlparse(origin_url)
        u = f'{url.scheme}://1:2@{url.host}:{url.port}{url.path}'
        yield Config(TRANSMISSION_RPC_URL=u)
    else:
        yield


@pytest.fixture()
def set_wrong_addr():
    with mock.patch(
        'bgmi.config.config_obj',
        Config(
            ARIA2_RPC_URL='http://127.0.0.1:6715/rpc',
            DELUGE_RPC_URL='http://127.0.0.1:6715/json',
            TRANSMISSION_RPC_URL='http://127.0.0.1:6715/transmission/rpc',
        )
    ):
        yield
