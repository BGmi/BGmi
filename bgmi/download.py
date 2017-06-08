# coding=utf-8
from __future__ import print_function, unicode_literals

import os

from bgmi.config import BGMI_SAVE_PATH, DOWNLOAD_DELEGATE
from bgmi.models import Download, STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD
from bgmi.services import XunleiLixianDownload, Aria2DownloadRPC, RRDownload, TransmissionRPC
from bgmi.utils.utils import print_error

DOWNLOAD_DELEGATE_DICT = {
    'xunlei': XunleiLixianDownload,
    'aria2-rpc': Aria2DownloadRPC,
    'transmission-rpc': TransmissionRPC,
    'rr!': RRDownload,
}


def get_download_class(download_obj=None, save_path='', overwrite=True, instance=True):
    if DOWNLOAD_DELEGATE not in DOWNLOAD_DELEGATE_DICT:
        print_error('unexpected delegate {0}'.format(DOWNLOAD_DELEGATE))

    delegate = DOWNLOAD_DELEGATE_DICT.get(DOWNLOAD_DELEGATE)

    if instance:
        delegate = delegate(download_obj=download_obj, overwrite=overwrite, save_path=save_path)

    return delegate


def download_prepare(data):
    queue = save_to_bangumi_download_queue(data)
    for download in queue:
        save_path = os.path.join(os.path.join(BGMI_SAVE_PATH, download.name), str(download.episode))
        # mark as downloading
        download.status = STATUS_DOWNLOADING
        download.save()
        try:
            # start download
            download_class = get_download_class(download_obj=download, save_path=save_path, overwrite=True)
            download_class.download()
            download_class.check_download(download.name)

            # mark as downloaded
            download.delete()
        except Exception as e:
            print_error('Error: {0}'.format(e), exit_=False)
            download.status = STATUS_NOT_DOWNLOAD
            download.save()


def save_to_bangumi_download_queue(data):
    queue = []
    for i in data:
        download = Download(status=STATUS_NOT_DOWNLOAD, name=i['name'], title=i['title'],
                            episode=i['episode'], download=i['download'])
        download.save()
        queue.append(download)

    return queue
