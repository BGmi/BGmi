from loguru import logger

from bgmi.plugin.download import BaseDownloadService, DownloadStatus


class Noop(BaseDownloadService):
    def __init__(self):
        pass

    def add_download(self, url: str, save_path: str):
        logger.info(f"noop downloader:\ndownloading {url=}\n{save_path=}")
        return None

    def get_status(self, id: str) -> DownloadStatus:
        return DownloadStatus.downloading
