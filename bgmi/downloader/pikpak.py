from pikpakapi import PikPakAPI
from pikpakapi.PikpakException import PikpakException,PikpakAccessTokenExpireException

from bgmi import config
from bgmi.plugin.download import BaseDownloadService, DownloadStatus


class PikPak(BaseDownloadService):
    def __init__(self):
        self.client = PikPakAPI(
            username=config.PIKPAK_USERNAME,
            password=config.PIKPAK_PASSWORD,
        )
        self.client.login()

    @staticmethod
    def check_config() -> None:
        pass

    @staticmethod
    def check_dep():
        pass

    def add_download(self, url: str, save_path: str):
        try:
            result = self.client.offline_download(
                urls=url,
            )
            return result.get("task").get("id") + "#" + result.get("task").get("file_id")
        except PikpakAccessTokenExpireException as e:
            self.client.login()
            result = self.client.offline_download(
                urls=url,
            )
            return result.get("task").get("id") + "#" + result.get("task").get("file_id")

        return None

    def get_status(self, id: str) -> DownloadStatus:
        task_id = id.split("#")[0]
        file_id = id.split("#")[1]
        infos = self.client.offline_list()
        if not infos:
            return DownloadStatus.not_found
        for task in infos.get("tasks"):
            if task_id == task.get("id"):
                return DownloadStatus.downloading
        try:
            file_info = self.client.offline_file_info(file_id=file_id)
            if file_info:
                return DownloadStatus.done
        except PikpakException as e:
            return DownloadStatus.error
