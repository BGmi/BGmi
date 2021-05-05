import transmission_rpc

from bgmi.config import (
    TRANSMISSION_RPC_PASSWORD,
    TRANSMISSION_RPC_PORT,
    TRANSMISSION_RPC_URL,
    TRANSMISSION_RPC_USERNAME,
)
from bgmi.downloader.base import BaseDownloadService
from bgmi.plugin.base import BaseDownloadService
from bgmi.plugin.status import DownloadStatus
from bgmi.website.model import Episode


class TransmissionRPC(BaseDownloadService):
    def __init__(self):
        super().__init__()

        self.client = transmission_rpc.Client(
            host=TRANSMISSION_RPC_URL,
            port=TRANSMISSION_RPC_PORT,
            username=TRANSMISSION_RPC_USERNAME,
            password=TRANSMISSION_RPC_PASSWORD,
        )

    def add_download(self, episode: Episode, save_path: str, overwrite: bool = False):
        torrent = self.client.add_torrent(
            episode.download, download_dir=save_path, paused=False
        )
        return torrent.hashString

    @staticmethod
    def check_dep():
        pass

    def get_status(self, id: str) -> DownloadStatus:
        torrent = self.client.get_torrent(id)
        if torrent.error:
            return DownloadStatus.error
        return {
            "check pending": DownloadStatus.downloading,
            "checking": DownloadStatus.downloading,
            "downloading": DownloadStatus.downloading,
            "seeding": DownloadStatus.done,
            "stopped": DownloadStatus.not_downloading,
        }.get(torrent.status, DownloadStatus.error)
