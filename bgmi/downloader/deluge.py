import uuid

import requests

from bgmi.downloader.base import AuthError, BaseDownloadService, ConnectError
from bgmi.utils import print_info


class DelugeRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = requests.session()
        self._url = self.config.DELUGE_RPC_URL
        res = self._call('auth.login', [
            self.config.DELUGE_RPC_PASSWORD,
        ])
        if not res['result']:
            raise AuthError('Deluge RPC require a password')

    def _call(self, methods, params):
        id = uuid.uuid4().hex
        try:

            r = self._session.post(
                self._url,
                headers={'Content-Type': 'application/json'},
                json={
                    'method': methods,
                    'params': params,
                    'id': id,
                },
                timeout=10,
            )
        except (requests.ConnectionError, requests.ConnectTimeout) as e:
            raise ConnectError() from e

        res = r.json()
        if res['error']:
            raise AuthError('deluge error, reason: {}'.format(res['error']['message']))

        return res

    def download(self, torrent: str, save_path: str):
        if not torrent.startswith('magnet:'):
            e = self._call('web.download_torrent_from_url', [
                torrent,
            ])
            torrent = e['result']
        options = {
            'path': torrent, 'options': {
                'add_paused': False,
                'compact_allocation': False,
                'move_completed': False,
                'download_location': save_path,
            }
        }

        self._call('web.add_torrents', [[options]])

        print_info(f'Add torrent into the download queue, the file will be saved at {save_path}')


if __name__ == '__main__':
    rpc_server = DelugeRPC()
