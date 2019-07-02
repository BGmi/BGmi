from bgmi.config import (
    TRANSMISSION_RPC_PASSWORD, TRANSMISSION_RPC_PORT, TRANSMISSION_RPC_URL,
    TRANSMISSION_RPC_USERNAME
)
from bgmi.downloader.base import BaseDownloadService, RequireNotSatisfied
from bgmi.utils import print_info


class TransmissionRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import transmission_rpc

        self.client = transmission_rpc.Client(
            TRANSMISSION_RPC_URL,
            port=TRANSMISSION_RPC_PORT,
            user=TRANSMISSION_RPC_USERNAME,
            password=TRANSMISSION_RPC_PASSWORD
        )

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
