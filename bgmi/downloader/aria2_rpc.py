import xmlrpc.client
from functools import wraps
from xmlrpc.client import ServerProxy

from bgmi.config import ARIA2_RPC_TOKEN, ARIA2_RPC_URL
from bgmi.downloader.base import AuthError, BaseDownloadService, ConnectError
from bgmi.lib.db_models import Download
from bgmi.utils import print_error, print_info, print_success, print_warning


def _unauthorized(func):
    """
    wrap xmlrpc.client exception to DownloadService exception
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpc.client.Fault as e:
            if e.faultCode == 401:
                raise AuthError(e.faultString)
            else:
                raise

    return wrapped


class Aria2DownloadRPC(BaseDownloadService):
    old_version: bool

    def __init__(self, *args, **kwargs):
        self.old_version = False
        self.server = ServerProxy(ARIA2_RPC_URL)
        self.check_aria2c_version()
        super().__init__(*args, **kwargs)

    @_unauthorized
    def download(self, torrent: str, save_path: str):
        try:

            if self.old_version:
                self.server.aria2.addUri([torrent], {'dir': save_path})
            else:
                self.server.aria2.addUri(ARIA2_RPC_TOKEN, [torrent], {'dir': save_path})
            print_info(
                f'Add torrent into the download queue, the file will be saved at {save_path}'
            )
        except (xmlrpc.client.ProtocolError, xmlrpc.client.ResponseError) as e:
            raise ConnectError() from e

    @_unauthorized
    def check_aria2c_version(self):
        url = ARIA2_RPC_URL.split('/')
        url[2] = ARIA2_RPC_TOKEN + '@' + url[2]
        url = '/'.join(url)
        r = ServerProxy(url).aria2.getVersion(ARIA2_RPC_TOKEN)
        version = r['version']
        if version:
            self.old_version = version < '1.18.4'
        else:
            print_warning('Get aria2c version failed')

    @_unauthorized
    def download_status(self, status=None):

        print_info('Print download status in database')
        super().download_status(status=status)
        print()
        print_info('Print download status in aria2c-rpc')
        try:
            # self.server.aria2
            status_dict = {
                Download.STATUS.DOWNLOADING: ['tellActive'],
                Download.STATUS.NOT_DOWNLOAD: ['tellWaiting'],
                Download.STATUS.DOWNLOADED: ['tellStopped'],
                None: ['tellStopped', 'tellWaiting', 'tellActive'],
            }
            for method in status_dict.get(status):
                if method not in ('tellActive', ):
                    params = (0, 1000)
                else:
                    params = ()
                if Aria2DownloadRPC.old_version:
                    data = getattr(self.server.aria2, method)(*params)
                else:
                    data = getattr(self.server.aria2, method)(ARIA2_RPC_TOKEN, *params)

                if data:
                    print_warning(f'RPC {method}:', indicator=False)

                for row in data:
                    print_success('- {}'.format(row['dir']), indicator=False)
                    for file_ in row['files']:
                        print_info('    * {}'.format(file_['path']), indicator=False)

        except Exception:
            print_error('Cannot connect to aria2-rpc server')
