from __future__ import print_function, unicode_literals

import requests

from bgmi.config import DELUGE_RPC_URL, DELUGE_RPC_PASSWORD
from bgmi.downloader.base import BaseDownloadService
from bgmi.utils import print_info, print_error


class DelugeRPC(BaseDownloadService):
    old_version = False

    def __init__(self, *args, **kwargs):
        self._id = 0
        self._session = requests.session()
        l = self._call('auth.login', [DELUGE_RPC_PASSWORD, ])
        super(DelugeRPC, self).__init__(**kwargs)

    def _call(self, methods, params):
        r = self._session.post(DELUGE_RPC_URL,
                               headers={'Content-Type': 'application/json'},
                               json={"method": methods, "params": params, "id": self._id},
                               timeout=10)

        self._id += 1
        e = r.json()
        if not e['result']:
            print_error('deluge error, reason: {}'.format(e['error']['message']), exit_=False)

        return e

    def download(self):
        if not self.torrent.startswith('magnet:'):
            # self._call("web.get_magnet_info", [self.torrent, ])
        # else:
            e = self._call('web.download_torrent_from_url', [self.torrent, ])
            self.torrent = e['result']
        options = {"path": self.torrent,
                   "options": {"add_paused": False,
                               "compact_allocation": False,
                               "move_completed": False,
                               "download_location": self.save_path,
                               "max_connections": -1,
                               "max_download_speed": -1,
                               "max_upload_slots": -1,
                               "max_upload_speed": -1,
                               }}
        e = self._call('web.add_torrents', [[options]])
        print_info('Add torrent into the download queue, the file will be saved at {0}'.format(self.save_path))

        return e

    @staticmethod
    def install():
        pass

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        pass


if __name__ == '__main__':
    class downloadObj(object):
        pass


    o = downloadObj()
    o.name = 'name'
    o.download = 'https://mikanani.me/Download/20180509/65ed60acc70e38983e564183311c9b0f47996313.torrent'
    o.episode = '1'
    e = DelugeRPC(download_obj=o, save_path='C:\\Users\\Trim21\\proj\\tmp\\bangumi')
    print(e.download())
