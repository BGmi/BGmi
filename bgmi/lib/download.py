import os
import xmlrpc.client
from functools import singledispatch

from bgmi.config import DOWNLOAD_DELEGATE, SAVE_PATH
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmissionRpc import TransmissionRPC
from bgmi.lib.models import Download
from bgmi.utils import normalize_path, print_error

DOWNLOAD_DELEGATE_DICT = {
    'aria2-rpc': Aria2DownloadRPC,
    'transmission-rpc': TransmissionRPC,
    'deluge-rpc': DelugeRPC,
}


def get_download_class(download_obj=None, save_path='', overwrite=True, instance=True):
    if DOWNLOAD_DELEGATE not in DOWNLOAD_DELEGATE_DICT:
        print_error('unexpected delegate {}'.format(DOWNLOAD_DELEGATE))

    delegate = DOWNLOAD_DELEGATE_DICT.get(DOWNLOAD_DELEGATE)

    if instance:
        delegate = delegate(download_obj=download_obj, overwrite=overwrite, save_path=save_path)

    return delegate


@singledispatch
def handle_specific_exception(e):  # got an exception we don't handle
    print_error('Error, {}'.format(e), exit_=False)


@handle_specific_exception.register(xmlrpc.client.Fault)
def _(e):
    # handle exception 1
    err_string = str(e)
    if 'Unauthorized' in err_string:
        print_error('aria2-rpc, wrong secret token', exit_=False)
    else:
        print_error('Error, {}'.format(e), exit_=False)


@handle_specific_exception.register(xmlrpc.client.ProtocolError)
def _(e):
    # handle exception 2
    print_error('can\'t connect to aria2-rpc server, {}'.format(e), exit_=False)


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
            download_class = get_download_class(download_obj=download, save_path=save_path)
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
