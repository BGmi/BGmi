# coding=utf-8
from __future__ import print_function, unicode_literals
import os
import subprocess
from bgmi.config import BGMI_LX_PATH, BGMI_SAVE_PATH
from bgmi.models import Download
from bgmi.utils import print_info


def download_prepare(data):
    save_to_bangumi_download_queue(data)
    download_xunlei_lixian(data)


def download_xunlei_lixian(data):
    for i in data:
        command = [BGMI_LX_PATH, 'download', '--torrent', '--overwrite',
                   '--output-dir=%s' % BGMI_SAVE_PATH, i['download']]
        print_info('Run command %s' % ' '.join(command))
        subprocess.call(command, env={'PATH': '/usr/local/bin:/usr/bin:/bin',
                                      'HOME': os.environ.get('HOME', '/tmp')})
        d = Download(**i)
        d.delete()


def save_to_bangumi_download_queue(data):
    for i in data:
        download = Download(**i)
        download.save()
