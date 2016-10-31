# coding=utf-8
from __future__ import unicode_literals, print_function

import os
import subprocess
from tempfile import NamedTemporaryFile

import bgmi.config
from bgmi.config import BGMI_LX_PATH, BGMI_PATH, BGMI_TMP_PATH, ARIA2_PATH, ARIA2_RPC_URL
from bgmi.utils.utils import print_warning, print_info, print_error, print_success
from bgmi.models import Download, STATUS_DOWNLOADED, STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING


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


#######################
#   DownloadService   #
#######################
class DownloadService(object):
    def __init__(self, download_obj, save_path, overwrite=True):
        self.name = download_obj.name
        self.torrent = download_obj.download
        self.overwrite = overwrite
        self.save_path = save_path
        self.episode = download_obj.episode

    def download(self):
        # download
        raise NotImplementedError

    @staticmethod
    def install():
        # install requirement
        raise NotImplementedError

    def check_path(self):
        if not os.path.exists(self.save_path):
            print_warning('Create dir {0}'.format(self.save_path))
            os.makedirs(self.save_path)

    def check_delegate_bin_exist(self, path):
        if not os.path.exists(path):
            print_error('{0} not exist, please run command \'bgmi install\' to install'.format(path))

    def call(self, command):
        subprocess.call(command, env={'PATH': '/usr/local/bin:/usr/bin:/bin',
                                      'HOME': os.environ.get('HOME', '/tmp')})

    def check_download(self, name):
        if not os.path.exists(self.save_path):
            raise Exception('It seems the bangumi {0} not be downloaded'.format(name))

    @staticmethod
    def download_status(status=None):
        last_status = -1
        for download_data in Download.get_all_downloads(status=status):
            latest_status = download_data['status']
            name = '  {0}. <{1}: {2}>'.format(download_data['id'], download_data['name'],
                                              download_data['episode'])
            if latest_status != last_status:
                if latest_status == STATUS_DOWNLOADING:
                    print('Downloading items:')
                elif latest_status == STATUS_NOT_DOWNLOAD:
                    print('Not downloaded items:')
                elif latest_status == STATUS_DOWNLOADED:
                    print('Downloaded items:')

            if download_data['status'] == STATUS_NOT_DOWNLOAD:
                print_info(name, indicator=False)
            elif download_data['status'] == STATUS_DOWNLOADING:
                print_warning(name, indicator=False)
            elif download_data['status'] == STATUS_DOWNLOADED:
                print_success(name, indicator=False)
            last_status = download_data['status']


class Aria2Download(DownloadService):
    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist(ARIA2_PATH)
        super(Aria2Download, self).__init__(*args, **kwargs)

    def download(self):
        command = [ARIA2_PATH, '--seed-time=0', '-d', self.save_path, self.torrent]
        print_info('Run command {0}'.format(' '.join(command)))
        self.call(command)

    @staticmethod
    def install():
        print_warning('Please install aria2 by yourself')


class Aria2DownloadRPC(DownloadService):
    def __init__(self, *args, **kwargs):
        self.server = PatchedServerProxy(ARIA2_RPC_URL)
        super(Aria2DownloadRPC, self).__init__(**kwargs)

    def download(self):
        self.server.aria2.addUri([self.torrent], {"dir": self.save_path})
        print_info('Add torrent into the download queue, the file will be saved at {0}'.format(self.save_path))

    @staticmethod
    def install():
        print_warning('Please install aria2 by yourself')

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        print_info('Print download status in database')
        DownloadService.download_status(status=status)
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
                data = server.aria2[method](*params)
                if data:
                    print_warning('RPC {0}:'.format(method), indicator=False)
                for row in data:
                    print_success('- {0}'.format(row['dir']), indicator=False)
                    for file in row['files']:
                        print_info('    * {0}'.format(file['path']), indicator=False)
        except Exception as e:
            print_error('Cannot connect to aria2-rpc server')


class XunleiLixianDownload(DownloadService):
    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist(BGMI_LX_PATH)
        super(XunleiLixianDownload, self).__init__(*args, **kwargs)

    def download(self):
        overwrite = '--overwrite' if self.overwrite else ''

        command = [BGMI_LX_PATH, 'download', '--torrent', overwrite,
                   '--output-dir={0}'.format(self.save_path), self.torrent,
                   '--verification-code-path={0}'.format(os.path.join(BGMI_TMP_PATH, 'vcode.jpg'))]

        print_info('Run command {0}'.format(' '.join(command)))
        print_warning('Verification code path: {0}'.format(os.path.join(BGMI_TMP_PATH, 'vcode.jpg')))
        self.call(command)

    @staticmethod
    def install():
        # install xunlei-lixian
        import tarfile
        import requests
        print_info('Downloading xunlei-lixian from https://github.com/iambus/xunlei-lixian/')
        r = requests.get('https://github.com/iambus/xunlei-lixian/tarball/master', stream=True,
                         headers={'Accept-Encoding': ''})
        f = NamedTemporaryFile(delete=False)

        with f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        f.close()
        print_success('Download successfully, save at %s, extracting ...' % f.name)
        zip_file = tarfile.open(f.name, 'r:gz')
        zip_file.extractall(os.path.join(BGMI_PATH, 'tools/xunlei-lixian'))
        dir_name = zip_file.getnames()[0]

        print_info('Create link file ...')

        if not os.path.exists(BGMI_LX_PATH):
            os.symlink(os.path.join(BGMI_PATH, 'tools/xunlei-lixian/{0}/lixian_cli.py'.format(dir_name)),
                       BGMI_LX_PATH)
        else:
            print_warning('{0} already exists'.format(BGMI_LX_PATH))

        print_success('All done')
        print_info('Please run command \'{0} config\' to configure your lixian-xunlei '
                   '(Notice: only for Thunder VIP)'.format(BGMI_LX_PATH))


#######################
#   SendMailService   #
#######################
class SendMailService(object):
    pass
