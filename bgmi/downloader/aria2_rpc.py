import xmlrpc.client

from bgmi import config
from bgmi.plugin.base import BaseDownloadService
from bgmi.plugin.status import DownloadStatus
from bgmi.utils import print_warning
from bgmi.website.model import Episode


class Aria2DownloadRPC(BaseDownloadService):
    def __init__(self):
        self.old_version = False
        self.server = xmlrpc.client.ServerProxy(config.ARIA2_RPC_URL)
        Aria2DownloadRPC.check_aria2c_version()
        super().__init__()

    def add_download(
        self, episode: Episode, save_path: str, overwrite: bool = False
    ) -> str:
        args = [[episode.download], {"dir": save_path}]
        if self.old_version:
            return self.server.aria2.addUri(*args)
        else:
            return self.server.aria2.addUri(config.ARIA2_RPC_TOKEN, *args)

    @staticmethod
    def check_dep():
        pass

    def get_status(self, id: str) -> DownloadStatus:
        args = (id, ["status"])
        if self.old_version:
            r = self.server.aria2.tellStatus(*args)
        else:
            r = self.server.aria2.tellStatus(config.ARIA2_RPC_TOKEN, *args)

        return {
            "waiting": DownloadStatus.downloading,
            "paused": DownloadStatus.not_downloading,
            "error": DownloadStatus.error,
            "complete": DownloadStatus.done,
        }.get(r["status"])

    def check_aria2c_version(self):
        url = config.ARIA2_RPC_URL.split("/")
        url[2] = config.ARIA2_RPC_TOKEN + "@" + url[2]
        url = "/".join(url)
        s = xmlrpc.client.ServerProxy(url)
        r = s.aria2.getVersion(config.ARIA2_RPC_TOKEN)
        version = r["version"]
        if version:
            self.old_version = [int(x) for x in version.split(".")] < [1, 18, 4]
        else:
            print_warning("Get aria2c version failed")
