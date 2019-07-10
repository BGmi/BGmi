import urllib.parse

import requests

from bgmi import config
from bgmi.downloader.base import BaseDownloadService, ConnectError, RequireNotSatisfied
from bgmi.utils import print_info


class TransmissionRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import transmission_rpc
        try:
            url_obj: urllib.parse.ParseResult = urllib.parse.urlparse(config.TRANSMISSION_RPC_URL)
            self.client = transmission_rpc.Client(
                url_obj.hostname,
                port=url_obj.port or config.TRANSMISSION_RPC_PORT,
                user=url_obj.username or config.TRANSMISSION_RPC_USERNAME,
                password=url_obj.password or config.TRANSMISSION_RPC_PASSWORD,
            )
            self.client.session_stats()
        except requests.ConnectionError as e:
            raise ConnectError from e

    @classmethod
    def require(cls):
        try:
            pass
        except ImportError:
            raise RequireNotSatisfied('Please run `pip install transmission-rpc`')

    def download(self, torrent: str, save_path: str):
        self.client.add_torrent(torrent, download_dir=save_path)
        print_info(
            'Add torrent into the download queue, '
            'the file will be saved at {}'.format(save_path)
        )

    def download_status(self, status=None):
        print_info('Print download status in database')
        BaseDownloadService.download_status(self, status=status)
        print('')
        print_info('Print download status in transmission-rpc')
        for torrent in self.client.get_torrents():
            print_info(f'  * {torrent.status}: {torrent}', indicator=False)
