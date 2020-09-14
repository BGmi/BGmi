import transmission_rpc

from bgmi.config import (
    TRANSMISSION_RPC_PASSWORD,
    TRANSMISSION_RPC_PORT,
    TRANSMISSION_RPC_URL,
    TRANSMISSION_RPC_USERNAME,
)
from bgmi.downloader.base import BaseDownloadService
from bgmi.utils import print_info, print_warning


class TransmissionRPC(BaseDownloadService):
    @staticmethod
    def get_client():
        return transmission_rpc.Client(
            host=TRANSMISSION_RPC_URL,
            port=TRANSMISSION_RPC_PORT,
            username=TRANSMISSION_RPC_USERNAME,
            password=TRANSMISSION_RPC_PASSWORD,
        )

    def download(self):
        tc = self.get_client()
        print(tc.add_torrent)
        tc.add_torrent(self.torrent, download_dir=self.save_path)

        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                self.save_path
            )
        )

    def check_download(self, name):
        pass

    @classmethod
    def download_status(cls, status=None):
        print_info("Print download status in database")
        BaseDownloadService.download_status(status=status)
        print("")
        print_info("Print download status in transmission-rpc")
        tc = cls.get_client()
        for torrent in tc.get_torrents():
            print_info(f"  * {torrent.status}: {torrent}", indicator=False)

    @staticmethod
    def install():
        try:
            __import__("transmission_rpc")
        except ImportError:
            print_warning("Please run `pip install transmission-rpc`")
