from __future__ import print_function, unicode_literals
import os
from tempfile import NamedTemporaryFile

from bgmi.downloader.base import BaseDownloadService
from bgmi.config import XUNLEI_LX_PATH, BGMI_PATH, TMP_PATH
from bgmi.utils import print_info, print_warning, print_success


class XunleiLixianDownload(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist(XUNLEI_LX_PATH)
        super(XunleiLixianDownload, self).__init__(*args, **kwargs)

    def download(self):
        print_warning('XunleiLixian is deprecated, please choose aria2-rpc or transmission-rpc.')
        overwrite = '--overwrite' if self.overwrite else ''

        command = [XUNLEI_LX_PATH, 'download', '--torrent', overwrite,
                   '--output-dir={0}'.format(self.save_path), self.torrent,
                   '--verification-code-path={0}'.format(os.path.join(TMP_PATH, 'vcode.jpg'))]

        print_info('Run command {0}'.format(' '.join(command)))
        print_warning('Verification code path: {0}'.format(os.path.join(TMP_PATH, 'vcode.jpg')))
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

        if not os.path.exists(XUNLEI_LX_PATH):
            os.symlink(os.path.join(BGMI_PATH, 'tools/xunlei-lixian/{0}/lixian_cli.py'.format(dir_name)),
                       XUNLEI_LX_PATH)
        else:
            print_warning('{0} already exists'.format(XUNLEI_LX_PATH))

        print_success('All done')
        print_info('Please run command \'{0} config\' to configure your lixian-xunlei '
                   '(Notice: only for Thunder VIP)'.format(XUNLEI_LX_PATH))
