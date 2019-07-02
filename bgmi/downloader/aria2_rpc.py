from xmlrpc.client import ServerProxy, _Method

from bgmi.config import ARIA2_RPC_TOKEN, ARIA2_RPC_URL
from bgmi.downloader.base import BaseDownloadService
from bgmi.lib.db_models import Download
from bgmi.utils import print_error, print_info, print_success, print_warning


class _PatchedMethod(_Method):
    def __getitem__(self, name):
        return _Method.__getattr__(self, name)

    def __getattr__(self, name):
        if name == '__getitem__':
            return self.__getitem__
        return _Method.__getattr__(self, name)

    def __call__(self, *args):
        print(args)


class PatchedServerProxy(ServerProxy):
    def __request(self, methodname, params):
        return ServerProxy._ServerProxy__request(self, methodname, params)

    def __getattr__(self, name):
        return _PatchedMethod(self.__request, name)


class Aria2DownloadRPC(BaseDownloadService):
    old_version: bool

    def __init__(self, *args, **kwargs):
        self.old_version = False
        self.server = PatchedServerProxy(ARIA2_RPC_URL)
        self.check_aria2c_version()
        super().__init__(*args, **kwargs)

    def download(self, torrent: str, save_path: str):
        if self.old_version:
            self.server.aria2.addUri([torrent], {'dir': save_path})
        else:
            self.server.aria2.addUri(ARIA2_RPC_TOKEN, [torrent], {'dir': save_path})
        print_info(f'Add torrent into the download queue, the file will be saved at {save_path}')

    def check_aria2c_version(self):
        url = ARIA2_RPC_URL.split('/')
        url[2] = ARIA2_RPC_TOKEN + '@' + url[2]
        url = '/'.join(url)
        r = self.server.aria2.getVersion(ARIA2_RPC_TOKEN)
        version = r['version']
        if version:
            self.old_version = version < '1.18.4'
        else:
            print_warning('Get aria2c version failed')

    def download_status(self, status=None):

        print_info('Print download status in database')
        BaseDownloadService.download_status(status=status)
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
                    data = self.server.aria2[method](*params)
                else:
                    data = self.server.aria2[method](ARIA2_RPC_TOKEN, *params)

                if data:
                    print_warning(f'RPC {method}:', indicator=False)

                for row in data:
                    print_success('- {}'.format(row['dir']), indicator=False)
                    for file_ in row['files']:
                        print_info('    * {}'.format(file_['path']), indicator=False)

        except BaseException:
            print_error('Cannot connect to aria2-rpc server')
