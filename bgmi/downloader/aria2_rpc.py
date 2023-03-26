import xmlrpc.client
from typing import cast

from bgmi.config import cfg
from bgmi.plugin.download import BaseDownloadService, DownloadStatus
from bgmi.utils import print_error, print_warning


class Aria2DownloadRPC(BaseDownloadService):
    def __init__(self):
        self.server = xmlrpc.client.ServerProxy(cfg.aria2.ARIA2_RPC_URL)
        if cfg.aria2.ARIA2_RPC_TOKEN.startswith("token:"):
            self.token = cfg.aria2.ARIA2_RPC_TOKEN
        else:
            self.token = "token:" + cfg.aria2.ARIA2_RPC_TOKEN

        s = xmlrpc.client.ServerProxy(cfg.ARIA2_RPC_URL)
        r = s.aria2.getVersion(cfg.aria2.ARIA2_RPC_TOKEN)
        version = r["version"]
        if version:
            old_version = [int(x) for x in version.split(".")] < [1, 18, 4]
            if old_version:
                print_error("you are using old aria2 version, please upgrade to it >1.18.4")
        else:
            print_warning("Get aria2c version failed")

    def add_download(self, url: str, save_path: str) -> str:
        args = [[url], {"dir": save_path}]
        return cast(str, self.server.aria2.addUri(self.token, *args))

    @staticmethod
    def check_dep():
        pass

    @staticmethod
    def check_config() -> None:
        if not cfg.aria2.ARIA2_RPC_URL.endswith("/rpc"):
            print_warning("make sure you are using xml-rpc endpoint of aria2")
        if not cfg.aria2.ARIA2_RPC_TOKEN.startswith("token:"):
            print_warning("rpc token should starts with `token:`")

    def get_status(self, id: str) -> DownloadStatus:
        args = (id, ["status"])
        r = self.server.aria2.tellStatus(self.token, *args)

        return {
            "active": DownloadStatus.downloading,
            "waiting": DownloadStatus.downloading,
            "paused": DownloadStatus.not_downloading,
            "error": DownloadStatus.error,
            "complete": DownloadStatus.done,
        }.get(r["status"], DownloadStatus.error)
