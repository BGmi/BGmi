from bgmi.config import (
    TRANSMISSION_RPC_PORT, TRANSMISSION_RPC_URL, TRANSMISSION_RPC_USERNAME,
    TRANSMISSION_RPC_PASSWORD
)

from bgmi.downloader.base import BaseDownloadService
from bgmi.utils import print_info, print_warning


class TransmissionRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist()
        super(TransmissionRPC, self).__init__(*args, **kwargs)

    def download(self):
        try:
            import transmission_rpc
            client = transmission_rpc.Client(
                TRANSMISSION_RPC_URL,
                port=TRANSMISSION_RPC_PORT,
                user=TRANSMISSION_RPC_USERNAME,
                password=TRANSMISSION_RPC_PASSWORD
            )
            client.add_torrent(self.torrent, download_dir=self.save_path)
            print_info(
                'Add torrent into the download queue, '
                'the file will be saved at {0}'.format(self.save_path)
            )
        except ImportError:
            self.install()

    def check_delegate_bin_exist(self):
        try:
            import transmission_rpc
        except ImportError:
            self.install()

    def check_download(self, name):
        pass

    @classmethod
    def download_status(cls, status=None):
        print_info('Print download status in database')
        BaseDownloadService.download_status(status=status)
        print('')
        print_info('Print download status in transmission-rpc')
        try:
            import transmission_rpc
            tc = transmission_rpc.Client(
                TRANSMISSION_RPC_URL,
                port=TRANSMISSION_RPC_PORT,
                user=TRANSMISSION_RPC_USERNAME,
                password=TRANSMISSION_RPC_PASSWORD
            )
            for torrent in tc.get_torrents():
                print_info('  * {0}: {1}'.format(torrent.status, torrent), indicator=False)
        except ImportError:
            cls.install()

    @staticmethod
    def install():
        print_warning('Please run `pip install transmission-rpc`')
