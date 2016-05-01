# coding=utf-8
from __future__ import print_function, unicode_literals
import subprocess
from bgmi.config import BGMI_LX_PATH, BGMI_SAVE_PATH
from bgmi.models import Download


def download_prepare(data):
    save_to_bangumi_download_queue(data)
    download_xunlei_lixian(data)


def download_xunlei_lixian(data):
    for i in data:
        subprocess.call([BGMI_LX_PATH, 'download', '--torrent', '--overwrite',
                         '--output-dir=%s' % BGMI_SAVE_PATH, i['download']])
        d = Download(**i)
        d.delete()


def save_to_bangumi_download_queue(data):
    for i in data:
        download = Download(**i)
        download.save()
