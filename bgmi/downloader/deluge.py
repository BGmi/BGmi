import requests

from bgmi import config
from bgmi.plugin.base import BaseDownloadService, RpcError
from bgmi.plugin.status import DownloadStatus
from bgmi.utils import print_info


class DelugeRPC(BaseDownloadService):
    def __init__(self):
        self._id = 0
        self._session = requests.session()
        self._call("auth.login", [config.DELUGE_RPC_PASSWORD])

    @staticmethod
    def check_config() -> None:
        pass

    @staticmethod
    def check_dep():
        pass

    def get_status(self, id: str) -> DownloadStatus:
        status = self._call("web.get_torrent_status", [id, ["state"]])

        return {
            "Error": DownloadStatus.error,
            "Downloading": DownloadStatus.downloading,
            "Paused": DownloadStatus.not_downloading,
            "Seeding": DownloadStatus.done,
        }.get(status["state"], DownloadStatus.error)

    def add_download(self, url: str, save_path: str, overwrite: bool = False):
        options = {
            "add_paused": False,
            "compact_allocation": False,
            "move_completed": False,
            "download_location": save_path,
            "max_connections": -1,
            "max_download_speed": -1,
            "max_upload_slots": -1,
            "max_upload_speed": -1,
        }
        e = self._call("core.add_torrent_url", [url, options])
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                save_path
            )
        )

        return e

    def _call(self, methods, params=None):
        if params is None:
            params = []
        r = self._session.post(
            config.DELUGE_RPC_URL,
            headers={"Content-Type": "application/json"},
            json={"method": methods, "params": params, "id": self._id},
            timeout=10,
        )

        self._id += 1
        e = r.json()
        print(e)

        if "result" not in e:
            raise RpcError("deluge error, reason: {}".format(e["error"]["message"]))

        return e["result"]
