import requests

from bgmi import config
from bgmi.downloader.base import BaseDownloadService
from bgmi.utils import print_error, print_info


class DelugeRPC(BaseDownloadService):
    old_version = False

    def __init__(self, *args, **kwargs):
        self._id = 0
        self._session = requests.session()
        self._call("auth.login", [config.DELUGE_RPC_PASSWORD])
        super().__init__(*args, **kwargs)

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

    def download(self):
        if not self.torrent.startswith("magnet:"):
            e = self._call("web.download_torrent_from_url", [self.torrent])
            self.torrent = e["result"]
        options = {
            "path": self.torrent,
            "options": {
                "add_paused": False,
                "compact_allocation": False,
                "move_completed": False,
                "download_location": self.save_path,
                "max_connections": -1,
                "max_download_speed": -1,
                "max_upload_slots": -1,
                "max_upload_speed": -1,
            },
        }
        e = self._call("web.add_torrents", [[options]])
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                self.save_path
            )
        )

        return e

    @staticmethod
    def install():
        pass

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        pass
