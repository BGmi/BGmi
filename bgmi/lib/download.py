import os
from typing import List, Type

from bgmi.config import DOWNLOAD_DELEGATE, SAVE_PATH
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.base import BaseDownloadService
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.qbittorrent import QBittorrentWebAPI
from bgmi.downloader.transmission import TransmissionRPC
from bgmi.downloader.xunlei import XunleiLixianDownload
from bgmi.lib.models import STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD, Download
from bgmi.utils import normalize_path, print_error
from bgmi.website.base import Episode

DOWNLOAD_DELEGATE_DICT = {
    "xunlei": XunleiLixianDownload,
    "aria2-rpc": Aria2DownloadRPC,
    "transmission-rpc": TransmissionRPC,
    "deluge-rpc": DelugeRPC,
    "qbittorrent-webapi": QBittorrentWebAPI,
}


def get_download_class() -> Type[BaseDownloadService]:
    try:
        return DOWNLOAD_DELEGATE_DICT[DOWNLOAD_DELEGATE]
    except KeyError:
        print_error(f"unexpected delegate {DOWNLOAD_DELEGATE}")
        raise


def get_download_instance(
    download_obj: Episode = None, save_path: str = "", overwrite: bool = True
) -> BaseDownloadService:
    cls = get_download_class()
    return cls(download_obj=download_obj, overwrite=overwrite, save_path=save_path)


def download_prepare(data: List[Episode]) -> None:
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
            os.path.join(SAVE_PATH, normalize_path(download.name)),
            str(download.episode),
        )
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # mark as downloading
        download.status = STATUS_DOWNLOADING
        download.save()
        try:
            # start download
            download_class = get_download_instance(
                download_obj=download, save_path=save_path
            )
            download_class.download()
            download_class.check_download(download.name)

            # mark as downloaded
            download.downloaded()
        except Exception as e:
            if os.getenv("DEBUG"):  # pragma: no cover
                import traceback

                traceback.print_exc()
                raise e

            print_error(f"Error: {e}", exit_=False)
            download.status = STATUS_NOT_DOWNLOAD
            download.save()


def save_to_bangumi_download_queue(data: List[Episode]) -> List[Download]:
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
            title=i.title,
            download=i.download,
            name=i.name,
            episode=i.episode,
            status=STATUS_NOT_DOWNLOAD,
        )

        queue.append(download)

    return queue
