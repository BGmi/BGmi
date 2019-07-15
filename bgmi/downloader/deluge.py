import uuid

import requests

from bgmi import config
from bgmi.downloader.base import AuthError, BaseDownloadService, ConnectError
from bgmi.utils import print_info


class DelugeRPC(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = requests.session()
        res = self._call('auth.login', [
            config.DELUGE_RPC_PASSWORD,
        ])
        if not res['result']:
            raise AuthError('Deluge RPC require a password')

    def _call(self, methods, params):
        id = uuid.uuid4().hex
        try:

            r = self._session.post(
                config.DELUGE_RPC_URL,
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

        e = r.json()
        if e['error']:
            raise AuthError('deluge error, reason: {}'.format(e['error']['message']))

        return e

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
