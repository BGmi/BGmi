import os
import xmlrpc.client
from functools import singledispatch
from typing import Type

import stevedore
import stevedore.exception

from bgmi.config import DOWNLOAD_DELEGATE, SAVE_PATH
from bgmi.downloader.base import BaseDownloadService
from bgmi.lib.constants import NameSpace
from bgmi.lib.models import Download
from bgmi.utils import normalize_path, print_error


def get_download_class() -> Type[BaseDownloadService]:
    try:
        cls = stevedore.DriverManager(NameSpace.download_delegate, DOWNLOAD_DELEGATE).driver
        return cls
    except stevedore.exception.NoMatches:
        print_error(f'unexpected delegate {DOWNLOAD_DELEGATE}')


@singledispatch
def handle_specific_exception(e):  # got an exception we don't handle
    print_error(f'Error, {e}', exit_=False)


@handle_specific_exception.register(xmlrpc.client.Fault)
def _(e):
    # handle exception 1
    err_string = str(e)
    if 'Unauthorized' in err_string:
        print_error('aria2-rpc, wrong secret token', exit_=False)
    else:
        print_error(f'Error, {e}', exit_=False)


@handle_specific_exception.register(xmlrpc.client.ProtocolError)
def _(e):
    # handle exception 2
    print_error(f'can\'t connect to aria2-rpc server, {e}', exit_=False)


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
        save_path = os.path.join(
            os.path.join(SAVE_PATH, normalize_path(download.name)), str(download.episode)
        )
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # mark as downloading
        download.status = Download.STATUS.DOWNLOADING
        download.save()

        try:
            # start download
            download_class = get_download_class()
            download_class = download_class(
                download_obj=download, overwrite=True, save_path=save_path
            )
            download_class.download()
            download_class.check_download(download.name)

            # mark as downloaded
            download.downloaded()

        except Exception as e:  # pylint: disable=W0703
            handle_specific_exception(e)

            download.status = Download.STATUS.NOT_DOWNLOAD
            download.save()

            if os.getenv('DEBUG'):  # pragma: no cover
                import traceback

                traceback.print_exc()
                raise e


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
        download, _ = Download.get_or_create(
            title=i['title'],
            download=i['download'],
            name=i['name'],
            episode=i['episode'],
            status=Download.STATUS.NOT_DOWNLOAD
        )

        queue.append(download)

    return queue
