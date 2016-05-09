# coding=utf-8
from __future__ import print_function, unicode_literals
import os
from bgmi.config import BGMI_SAVE_PATH, DOWNLOAD_DELEGATE
from bgmi.models import Download, STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD
from bgmi.services import XunleiLixianDownload
from bgmi.utils import print_error


DOWNLOAD_DELEGATE_DICT = {
    'xunlei': XunleiLixianDownload,
}


def get_download_class(torrent='', overwrite=True, save_path='', instance=True):
    if DOWNLOAD_DELEGATE not in DOWNLOAD_DELEGATE_DICT:
        print_error('unexpected download delegate {0}'.format(DOWNLOAD_DELEGATE))

    delegate = DOWNLOAD_DELEGATE_DICT.get(DOWNLOAD_DELEGATE)\

    if instance:
        delegate = delegate(torrent=torrent, overwrite=overwrite, save_path=save_path)

    return delegate


def download_prepare(data):
    queue = save_to_bangumi_download_queue(data)
    download_xunlei_lixian(queue)


def download_xunlei_lixian(queue):
    for download in queue:

        save_path = os.path.join(BGMI_SAVE_PATH, download.title)
        # mark as downloading
        download.status = STATUS_DOWNLOADING
        download.save()

        try:
            # start download
            download_class = get_download_class(torrent=download.download, overwrite=True, save_path=save_path)
            download_class.download()

            # mark as downloaded
            download.delete()
        except Exception as e:
            print_error('Error: {0}'.format(e))
        except KeyboardInterrupt:
            print_error('You pressed Ctrl+C, exit')


def save_to_bangumi_download_queue(data):
    queue = []
    for i in data:
        download = Download(status=STATUS_NOT_DOWNLOAD, **i)
        download.save()
        queue.append(download)

    return queue
