import requests

from bgmi.downloader.base import AuthError, BaseDownloadService, ConnectError, RequireNotSatisfied
from bgmi.utils import print_info


class TransmissionRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import transmission_rpc
        try:
            self.client = transmission_rpc.Client(
                protocol=self.config.TRANSMISSION_RPC_URL.scheme,
                host=self.config.TRANSMISSION_RPC_URL.host,
                path=self.config.TRANSMISSION_RPC_URL.path,
                port=self.config.TRANSMISSION_RPC_URL.port,
                username=self.config.TRANSMISSION_RPC_URL.user,
                password=self.config.TRANSMISSION_RPC_URL.password,
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
