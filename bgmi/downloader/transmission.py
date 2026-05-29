from typing import Any, List

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
        kwargs: dict[str, Any] = {"download_dir": save_path, "paused": False}
        if self.client.rpc_version >= 16:
            kwargs["labels"] = cfg.transmission.labels
        torrent = self.client.add_torrent(url, **kwargs)
        return torrent.hashString

    def get_status(self, id: str) -> DownloadStatus:
        torrent = self.client.get_torrent(id)
        if torrent.error:
            return DownloadStatus.not_found
        if torrent.status == "stopped":
            return DownloadStatus.done if torrent.progress == 100 else DownloadStatus.not_downloading
        return {
            "check pending": DownloadStatus.downloading,
            "checking": DownloadStatus.downloading,
            "downloading": DownloadStatus.downloading,
            "seeding": DownloadStatus.done,
        }.get(torrent.status, DownloadStatus.error)

    def get_files(self, id: str) -> List[str]:
        torrent = self.client.get_torrent(id)
        download_dir = torrent.download_dir or ""
        return [f"{download_dir}/{f.name}" for f in torrent.get_files()]

    def remove_download(self, id: str) -> None:
        self.client.remove_torrent(id)
