import qbittorrentapi
from qbittorrentapi import TorrentStates

from bgmi.config import (
    QBITTORRENT_CATEGORY,
    QBITTORRENT_HOST,
    QBITTORRENT_PASSWORD,
    QBITTORRENT_PORT,
    QBITTORRENT_USERNAME,
)
from bgmi.downloader.base import BaseDownloadService
from bgmi.plugin.base import BaseDownloadService
from bgmi.plugin.status import DownloadStatus
from bgmi.utils import print_info
from bgmi.website.model import Episode


class QBittorrentWebAPI(BaseDownloadService):
    def __init__(self):
        super().__init__()

        self.client = qbittorrentapi.Client(
            host=QBITTORRENT_HOST,
            port=QBITTORRENT_PORT,
            username=QBITTORRENT_USERNAME,
            password=QBITTORRENT_PASSWORD,
        )
        self.client.auth_log_in()

    def add_download(self, episode: Episode, save_path: str, overwrite: bool = False):
        self.client.torrents_add(
            urls=episode.download,
            category=QBITTORRENT_CATEGORY,
            save_path=save_path,
            is_paused=False,
            use_auto_torrent_management=False,
        )
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                save_path
            )
        )

    def check_download(self, name):
        pass

    @classmethod
    def download_status(cls, status=None):
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
    def check_dep():
        pass

    def get_status(self, id: str) -> DownloadStatus:

        # torrent in self.client.torrents_info(category=QBITTORRENT_CATEGORY)
        torrent = self.client.torrents.info()
        state_enum: "TorrentStates" = torrent.state_enum
        if state_enum.is_complete or state_enum.is_uploading:
            return DownloadStatus.done
        elif state_enum.is_errored:
            return DownloadStatus.error
        elif state_enum.is_downloading:
            return DownloadStatus.downloading
        elif state_enum == qbittorrentapi.TorrentStates.PAUSED_DOWNLOAD:
            return DownloadStatus.not_downloading
