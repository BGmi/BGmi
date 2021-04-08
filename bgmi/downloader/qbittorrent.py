from bgmi.config import (
    QBITTORRENT_CATEGORY,
    QBITTORRENT_HOST,
    QBITTORRENT_PASSWORD,
    QBITTORRENT_PORT,
    QBITTORRENT_USERNAME,
)
from bgmi.downloader.base import BaseDownloadService
from bgmi.utils import print_info, print_warning


class QBittorrentWebAPI(BaseDownloadService):
    @staticmethod
    def get_client():
        import qbittorrentapi

        qc = qbittorrentapi.Client(
            host=QBITTORRENT_HOST,
            port=QBITTORRENT_PORT,
            username=QBITTORRENT_USERNAME,
            password=QBITTORRENT_PASSWORD,
        )
        qc.auth_log_in()
        return qc

    def download(self):
        qc = self.get_client()
        qc.torrents_add(
            urls=self.torrent,
            category=QBITTORRENT_CATEGORY,
            save_path=self.save_path,
            is_paused=False,
            use_auto_torrent_management=False,
        )
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                self.save_path
            )
        )

    def check_download(self, name):
        pass

    @classmethod
    def download_status(cls, status=None):
        import qbittorrentapi

        print_info("Print download status in database")
        BaseDownloadService.download_status(status=status)
        print("")
        print_info("Print download status in qbittorrent-webapi")
        qc = cls.get_client()
        for torrent in qc.torrents_info(category=QBITTORRENT_CATEGORY):
            state_enum = qbittorrentapi.TorrentStates(torrent.state)
            print_info(
                "  * {}:\t{}\t [{}%]".format(
                    state_enum.value, torrent.name, torrent.progress * 100
                ),
                indicator=False,
            )

    @staticmethod
    def install():
        try:
            __import__("qbittorrentapi")
        except ImportError:
            print_warning("Please run `pip install qbittorrent-api`")
