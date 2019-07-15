import urllib.parse

import requests

from bgmi import config
from bgmi.downloader.base import AuthError, BaseDownloadService, ConnectError, RequireNotSatisfied
from bgmi.utils import print_info


class TransmissionRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import transmission_rpc
        try:
            url_obj: urllib.parse.ParseResult = urllib.parse.urlparse(config.TRANSMISSION_RPC_URL)

            self.client = transmission_rpc.Client(
                protocol=url_obj.scheme,
                host=url_obj.hostname,
                path=url_obj.path,
                port=url_obj.port,
                username=url_obj.username,
                password=url_obj.password,
            )
        except transmission_rpc.TransmissionError as e:
            if e.original.status_code == 401:
                raise AuthError from e
        except requests.ConnectionError as e:
            raise ConnectError from e

    @classmethod
    def require(cls):
        try:
            import transmission_rpc
            assert 3 >= int(transmission_rpc.__version__.split('.')[0]) >= 2
        except (ImportError, AssertionError):
            raise RequireNotSatisfied('Please run `pip install "transmission-rpc>=2.0.0,<3.0.0"`')

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
