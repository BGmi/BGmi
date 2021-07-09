import xmlrpc.client
from typing import cast

from bgmi import config
from bgmi.plugin.base import BaseDownloadService
from bgmi.plugin.status import DownloadStatus
from bgmi.utils import print_warning


class Aria2DownloadRPC(BaseDownloadService):
    def __init__(self):
        self.old_version = False
        self.server = xmlrpc.client.ServerProxy(config.ARIA2_RPC_URL)
        self.check_aria2c_version()

    def add_download(self, url: str, save_path: str, overwrite: bool = False) -> str:
        args = [[url], {"dir": save_path}]
        if self.old_version:
            return cast(str, self.server.aria2.addUri(*args))
        return cast(str, self.server.aria2.addUri(config.ARIA2_RPC_TOKEN, *args))

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
        }.get(r["status"], DownloadStatus.error)

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
