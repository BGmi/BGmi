import os
import traceback
from typing import Dict, List, Type

from bgmi.config import DOWNLOAD_DELEGATE, SAVE_PATH
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.qbittorrent import QBittorrentWebAPI
from bgmi.downloader.transmission import TransmissionRPC
from bgmi.lib.models import STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD, Download
from bgmi.plugin.base import BaseDownloadService
from bgmi.utils import normalize_path, print_error
from bgmi.website.base import Episode

DOWNLOAD_DELEGATE_DICT: Dict[str, Type[BaseDownloadService]] = {
    "aria2-rpc": Aria2DownloadRPC,
    "transmission-rpc": TransmissionRPC,
    "deluge-rpc": DelugeRPC,
    "qbittorrent-webapi": QBittorrentWebAPI,
}


def get_download_driver() -> BaseDownloadService:
    try:
        return DOWNLOAD_DELEGATE_DICT[DOWNLOAD_DELEGATE]()
    except KeyError:
        print_error(f"unexpected delegate {DOWNLOAD_DELEGATE}")
        raise


def download_prepare(data: List[Episode]) -> None:
    queue = save_to_bangumi_download_queue(data)
    driver = get_download_driver()
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
            driver.add_download(url=download.download, save_path=save_path)
        except Exception as e:
            if os.getenv("DEBUG"):  # pragma: no cover

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
