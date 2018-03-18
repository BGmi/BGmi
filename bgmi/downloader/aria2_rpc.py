from __future__ import print_function, unicode_literals
import bgmi.config
from bgmi.downloader.base import BaseDownloadService
from bgmi.config import ARIA2_RPC_URL, ARIA2_RPC_TOKEN
from bgmi.utils import print_info, print_warning, print_success, print_error
from bgmi.lib.models import STATUS_DOWNLOADED, STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING


if bgmi.config.IS_PYTHON3:
    from xmlrpc.client import ServerProxy, _Method
else:
    from xmlrpclib import ServerProxy, _Method


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
    old_version = False

    def __init__(self, *args, **kwargs):
        self.server = PatchedServerProxy(ARIA2_RPC_URL)
        Aria2DownloadRPC.check_aria2c_version()
        super(Aria2DownloadRPC, self).__init__(**kwargs)

    def download(self):
        if self.old_version:
            self.server.aria2.addUri([self.torrent], {"dir": self.save_path})
        else:
            self.server.aria2.addUri(ARIA2_RPC_TOKEN, [self.torrent], {"dir": self.save_path})
        print_info('Add torrent into the download queue, the file will be saved at {0}'.format(self.save_path))

    @staticmethod
    def check_aria2c_version():
        url = ARIA2_RPC_URL.split('/')
        url[2] = ARIA2_RPC_TOKEN + '@' + url[2]
        url = '/'.join(url)
        s = ServerProxy(url)
        r = s.aria2.getVersion(ARIA2_RPC_TOKEN, )
        version = r['version']
        if version:
            Aria2DownloadRPC.old_version = version < '1.18.4'
        else:
            print_warning('Get aria2c version failed')

    @staticmethod
    def install():
        print_warning('Please install aria2 by yourself')

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        Aria2DownloadRPC.check_aria2c_version()

        print_info('Print download status in database')
        BaseDownloadService.download_status(status=status)
        print()
        print_info('Print download status in aria2c-rpc')
        try:
            server = PatchedServerProxy(ARIA2_RPC_URL)
            # self.server.aria2
            status_dict = {
                STATUS_DOWNLOADING: ['tellActive'],
                STATUS_NOT_DOWNLOAD: ['tellWaiting'],
                STATUS_DOWNLOADED: ['tellStopped'],
                None: ['tellStopped', 'tellWaiting', 'tellActive'],
            }
            for method in status_dict.get(status):
                if method not in ('tellActive', ):
                    params = (0, 1000)
                else:
                    params = ()
                if Aria2DownloadRPC.old_version:
                    data = server.aria2[method](*params)
                else:
                    data = server.aria2[method](ARIA2_RPC_TOKEN, *params)

                if data:
                    print_warning('RPC {0}:'.format(method), indicator=False)

                for row in data:
                    print_success('- {0}'.format(row['dir']), indicator=False)
                    for file_ in row['files']:
                        print_info('    * {0}'.format(file_['path']), indicator=False)

        except Exception as e:
            print_error('Cannot connect to aria2-rpc server')
