# coding=utf-8
from __future__ import unicode_literals, print_function

import os
import subprocess
from tempfile import NamedTemporaryFile

from bgmi.config import BGMI_LX_PATH, BGMI_PATH, BGMI_TMP_PATH, ARIA2_PATH
from bgmi.utils.utils import print_warning, print_info, print_error, print_success


#######################
#   DownloadService   #
#######################
class DownloadService(object):
    def __init__(self, torrent, overwrite, save_path):
        self.torrent = torrent
        self.overwrite = overwrite
        self.save_path = save_path

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


class Aria2Download(DownloadService):
    def __init__(self, torrent, overwrite, save_path):
        self.check_delegate_bin_exist(ARIA2_PATH)
        super(Aria2Download, self).__init__(torrent, overwrite, save_path)

    def download(self):
        command = [ARIA2_PATH, '--seed-time=0', '-d', self.save_path, self.torrent]
        print_info('Run command {0}'.format(' '.join(command)))
        self.call(command)

    @staticmethod
    def install():
        print_warning('Please install aria2 by yourself')


class XunleiLixianDownload(DownloadService):
    def __init__(self, torrent, overwrite, save_path):
        self.check_delegate_bin_exist(BGMI_LX_PATH)
        super(XunleiLixianDownload, self).__init__(torrent, overwrite, save_path)

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
