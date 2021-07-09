import transmission_rpc

from bgmi import config
from bgmi.plugin.base import BaseDownloadService
from bgmi.plugin.status import DownloadStatus


class TransmissionRPC(BaseDownloadService):
    def __init__(self):
        self.client = transmission_rpc.Client(
            host=config.TRANSMISSION_RPC_URL,
            port=config.TRANSMISSION_RPC_PORT,
            username=config.TRANSMISSION_RPC_USERNAME,
            password=config.TRANSMISSION_RPC_PASSWORD,
        )

    @staticmethod
    def check_config() -> None:
        pass

    @staticmethod
    def check_dep():
        pass

    def add_download(self, url: str, save_path: str, overwrite: bool = False):
        torrent = self.client.add_torrent(url, download_dir=save_path, paused=False)
        return torrent.hashString

    def get_status(self, id: str) -> DownloadStatus:
        torrent = self.client.get_torrent(id)
        if torrent.error:
            return DownloadStatus.not_found
        return {
            "check pending": DownloadStatus.downloading,
            "checking": DownloadStatus.downloading,
            "downloading": DownloadStatus.downloading,
            "seeding": DownloadStatus.done,
            "stopped": DownloadStatus.not_downloading,
        }.get(torrent.status, DownloadStatus.error)
