# coding=utf-8
from __future__ import print_function, unicode_literals

import glob
import os

from bgmi.config import SAVE_PATH, DOWNLOAD_DELEGATE
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmission_rpc import TransmissionRPC
from bgmi.downloader.xunlei import XunleiLixianDownload
from bgmi.lib.models import STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD, Download
from bgmi.utils import print_error, normalize_path

DOWNLOAD_DELEGATE_DICT = {
    'xunlei': XunleiLixianDownload,
    'aria2-rpc': Aria2DownloadRPC,
    'transmission-rpc': TransmissionRPC,
    'deluge-rpc': DelugeRPC,
}


def get_download_class(download_obj=None, save_path='', overwrite=True, instance=True):
    if DOWNLOAD_DELEGATE not in DOWNLOAD_DELEGATE_DICT:
        print_error('unexpected delegate {0}'.format(DOWNLOAD_DELEGATE))

    delegate = DOWNLOAD_DELEGATE_DICT.get(DOWNLOAD_DELEGATE)

    if instance:
        delegate = delegate(download_obj=download_obj, overwrite=overwrite, save_path=save_path)

    return delegate


def download_prepare(data):
    """
    list[dict]
    dict[
    name:str, keyword you use when search
    title:str, title of episode
    episode:int, episode of bangumi
    download:str, link to download
    ]
    :param data:
    :return:
    """
    queue = save_to_bangumi_download_queue(data)
    for download in queue:
        save_path = os.path.join(os.path.join(SAVE_PATH, normalize_path(download.name)), str(download.episode))
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # mark as downloading
        download.status = STATUS_DOWNLOADING
        download.save()
        try:
            # start download
            download_class = get_download_class(download_obj=download, save_path=save_path)
            download_class.download()
            download_class.check_download(download.name)

            # mark as downloaded
            download.downloaded()
        except Exception as e:
            if os.getenv('DEBUG'):  # pragma: no cover
                import traceback

                traceback.print_exc()
                raise e

            print_error('Error: {0}'.format(e), exit_=False)
            download.status = STATUS_NOT_DOWNLOAD
            download.save()


def save_to_bangumi_download_queue(data):
    """
    list[dict]
    dict:{
    name;str, keyword you use when search
    title:str, title of episode
    episode:int, episode of bangumi
    download:str, link to download
    }
    :param data:
    :return:
    """
    queue = []
    for i in data:
        download, _ = Download.get_or_create(title=i['title'], download=i['download'],
                                             name=i['name'], episode=i['episode'],
                                             status=STATUS_NOT_DOWNLOAD)

        queue.append(download)

    return queue
