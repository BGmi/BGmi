from bgmi.downloader.base import BaseDownloadService
from bgmi.config import TRANSMISSION_RPC_PORT, TRANSMISSION_RPC_URL
from bgmi.utils import print_info, print_warning


class TransmissionRPC(BaseDownloadService):

    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist('')
        super(TransmissionRPC, self).__init__(*args, **kwargs)

    def download(self):
        try:
            import transmissionrpc
            tc = transmissionrpc.Client(TRANSMISSION_RPC_URL, port=TRANSMISSION_RPC_PORT)
            tc.add_torrent(self.torrent, download_dir=self.save_path.encode('utf-8'))
            print_info('Add torrent into the download queue, the file will be saved at {0}'.format(self.save_path))
        except ImportError:
            pass

    def check_delegate_bin_exist(self, path):
        try:
            import transmissionrpc
        except ImportError:
            raise Exception('Please run `pip install transmissionrpc`')

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        print_info('Print download status in database')
        BaseDownloadService.download_status(status=status)
        print()
        print_info('Print download status in transmission-rpc')
        try:
            import transmissionrpc
            tc = transmissionrpc.Client(TRANSMISSION_RPC_URL, port=TRANSMISSION_RPC_PORT)
            for torrent in tc.get_torrents():
                print_info('  * {0}: {1}'.format(torrent.status, torrent), indicator=False)
        except ImportError:
            pass

    @staticmethod
    def install():
        print_warning('Please run `pip install transmissionrpc`')
