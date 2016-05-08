# coding=utf-8
from __future__ import unicode_literals, print_function
import os
import subprocess
from bgmi.utils import print_warning, print_info, print_error
from bgmi.config import BGMI_LX_PATH


class DownloadService(object):
    def __init__(self, torrent, overwrite, save_path):
        self.torrent = torrent
        self.overwrite = overwrite
        self.save_path = save_path

    def download(self):
        raise NotImplementedError

    def check_path(self):
        if not os.path.exists(self.save_path):
            print_warning('Create dir {0}'.format(self.save_path))
            os.makedirs(self.save_path)

    def check_delegate_bin_exist(self, path):
        if not os.path.exists(path):
            print_error('{0} not exist, please run command \'bgmi install\' to install'.format(path))


class XunleiLixianDownload(DownloadService):
    def __init__(self, torrent, overwrite, save_path):
        self.check_delegate_bin_exist(BGMI_LX_PATH)
        super(XunleiLixianDownload, self).__init__(torrent, overwrite, save_path)

    def download(self):
        overwrite = '--overwrite' if self.overwrite else ''

        command = [BGMI_LX_PATH, 'download', '--torrent', overwrite,
                   '--output-dir={0}'.format(self.save_path), self.torrent]

        print_info('Run command {0}'.format(' '.join(command)))
        subprocess.call(command, env={'PATH': '/usr/local/bin:/usr/bin:/bin',
                                      'HOME': os.environ.get('HOME', '/tmp')})
