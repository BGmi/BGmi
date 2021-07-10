import os
import traceback
from typing import List, cast

import stevedore
from stevedore.exception import NoMatches

from bgmi import namespace
from bgmi.config import DOWNLOAD_DELEGATE, SAVE_PATH
from bgmi.lib.models import STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD, Download
from bgmi.plugin.download import BaseDownloadService
from bgmi.utils import normalize_path, print_error, print_info
from bgmi.website.base import Episode


def get_download_driver(delegate: str) -> BaseDownloadService:
    try:
        return cast(
            BaseDownloadService,
            stevedore.DriverManager(
                namespace.DOWNLOAD_DELEGATE, name=delegate, invoke_on_load=True
            ).driver,
        )
    except NoMatches:
        print_error(f"can't load download delegate {delegate}")
        raise


def download_prepare(data: List[Episode]) -> None:
    queue = save_to_bangumi_download_queue(data)
    driver = get_download_driver(DOWNLOAD_DELEGATE)
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
            print_info(
                "Add torrent into the download queue, "
                f"the file will be saved at {save_path}"
            )
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
