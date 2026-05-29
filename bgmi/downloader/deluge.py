from typing import List

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
        status = self._call("web.get_torrent_status", [id, ["state", "progress"]])

        if not status or "state" not in status:
            return DownloadStatus.not_found

        state = status["state"]
        if state == "Paused":
            return DownloadStatus.done if status.get("progress") == 100 else DownloadStatus.not_downloading
        return {
            "Error": DownloadStatus.error,
            "Downloading": DownloadStatus.downloading,
            "Checking": DownloadStatus.downloading,
            "Seeding": DownloadStatus.done,
        }.get(state, DownloadStatus.error)

    def add_download(self, url: str, save_path: str):
        options = {
            "add_paused": False,
            "move_completed": False,
            "download_location": save_path,
        }
        if url.startswith("magnet:"):
            return self._call("core.add_torrent_magnet", [url, options])
        return self._call("core.add_torrent_url", [url, options])

    def get_files(self, id: str) -> List[str]:
        status = self._call("web.get_torrent_status", [id, ["save_path", "files"]])
        save_path = status.get("save_path", "")
        files = status.get("files", [])
        return [f"{save_path}/{f['path']}" for f in files]

    def remove_download(self, id: str) -> None:
        self._call("core.remove_torrent", [id, False])

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
            raise RpcError(f"deluge error, reason: {e['error']['message']}")

        return e["result"]
