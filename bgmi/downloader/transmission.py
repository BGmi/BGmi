import transmission_rpc

from bgmi.config import cfg
from bgmi.plugin.download import BaseDownloadService, DownloadStatus


class TransmissionRPC(BaseDownloadService):
    def __init__(self):
        self.client = transmission_rpc.Client(
            host=cfg.transmission.rpc_host,
            port=cfg.transmission.rpc_port,
            username=cfg.transmission.rpc_username,
            password=cfg.transmission.rpc_password,
            path=cfg.transmission.rpc_path,
        )

    @staticmethod
    def check_config() -> None:
        pass

    def add_download(self, url: str, save_path: str):
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
