import requests

from bgmi.config import cfg
from bgmi.plugin.download import BaseDownloadService, DownloadStatus, RpcError


class DelugeRPC(BaseDownloadService):
    def __init__(self):
        self._id = 0
        self._session = requests.session()
        self._call("auth.login", [cfg.deluge.rpc_password])

    @staticmethod
    def check_config() -> None:
        pass

    def get_status(self, id: str) -> DownloadStatus:
        status = self._call("web.get_torrent_status", [id, ["state"]])

        return {
            "Error": DownloadStatus.error,
            "Downloading": DownloadStatus.downloading,
            "Paused": DownloadStatus.not_downloading,
            "Seeding": DownloadStatus.done,
        }.get(status["state"], DownloadStatus.error)

    def add_download(self, url: str, save_path: str):
        options = {
            "add_paused": False,
            "move_completed": False,
            "download_location": save_path,
        }
        e = self._call("core.add_torrent_url", [url, options])
        return e

    def _call(self, methods, params=None):
        if params is None:
            params = []
        r = self._session.post(
            cfg.deluge.rpc_url,
            headers={"Content-Type": "application/json"},
            json={"method": methods, "params": params, "id": self._id},
            timeout=10,
        )

        self._id += 1
        e = r.json()

        if "result" not in e:
            raise RpcError("deluge error, reason: {}".format(e["error"]["message"]))

        return e["result"]
