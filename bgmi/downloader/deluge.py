import requests

from bgmi import config
from bgmi.plugin.base import BaseDownloadService
from bgmi.plugin.status import DownloadStatus
from bgmi.utils import print_error, print_info
from bgmi.website.model import Episode


class DelugeRPC(BaseDownloadService):
    @staticmethod
    def check_dep():
        pass

    def get_status(self, id: str) -> DownloadStatus:
        self._call("web.get_torrent_status", [[{}]])

    def __init__(self):
        super().__init__()
        self._id = 0
        self._session = requests.session()
        self._call("auth.login", [config.DELUGE_RPC_PASSWORD])

    def add_download(self, episode: Episode, save_path: str, overwrite: bool = False):
        torrent = episode.download
        if not torrent.startswith("magnet:"):
            e = self._call("web.download_torrent_from_url", [torrent])
            torrent = e["result"]
        options = {
            "path": torrent,
            "options": {
                "add_paused": False,
                "compact_allocation": False,
                "move_completed": False,
                "download_location": save_path,
                "max_connections": -1,
                "max_download_speed": -1,
                "max_upload_slots": -1,
                "max_upload_speed": -1,
            },
        }
        e = self._call("web.add_torrents", [[options]])
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                torrent
            )
        )

        return e

    def _call(self, methods, params):
        r = self._session.post(
            config.DELUGE_RPC_URL,
            headers={"Content-Type": "application/json"},
            json={"method": methods, "params": params, "id": self._id},
            timeout=10,
        )

        self._id += 1
        e = r.json()
        if not e["result"]:
            print_error(
                "deluge error, reason: {}".format(e["error"]["message"]), exit_=False
            )
        return e
