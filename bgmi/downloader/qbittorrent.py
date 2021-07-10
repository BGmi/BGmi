import qbittorrentapi
from qbittorrentapi import TorrentStates

from bgmi import config
from bgmi.plugin.download import BaseDownloadService, DownloadStatus


class QBittorrentWebAPI(BaseDownloadService):
    def __init__(self):
        self.client = qbittorrentapi.Client(
            host=config.QBITTORRENT_HOST,
            port=config.QBITTORRENT_PORT,
            username=config.QBITTORRENT_USERNAME,
            password=config.QBITTORRENT_PASSWORD,
        )
        self.client.auth_log_in()

    @staticmethod
    def check_config() -> None:
        pass

    @staticmethod
    def check_dep():
        pass

    def add_download(self, url: str, save_path: str):
        self.client.torrents_add(
            urls=url,
            category=config.QBITTORRENT_CATEGORY,
            save_path=save_path,
            is_paused=False,
            use_auto_torrent_management=False,
        )

        info = self.client.torrents_info(sort="added_on")

        if info:
            for torrent in info:
                if torrent.save_path == save_path:
                    return torrent.hash
            return info[-1].hash
        return None

    def get_status(self, id: str) -> DownloadStatus:
        torrent = self.client.torrents.info(torrent_hashes=id)
        if not torrent:
            return DownloadStatus.not_found
        state_enum: TorrentStates = torrent[0].state_enum
        if state_enum.is_complete or state_enum.is_uploading:
            return DownloadStatus.done
        if state_enum.is_errored:
            return DownloadStatus.error
        if state_enum.is_paused:
            return DownloadStatus.not_downloading
        if state_enum.is_downloading or state_enum.is_checking:
            return DownloadStatus.downloading
        return DownloadStatus.error
