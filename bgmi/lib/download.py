import os
import traceback
from typing import List, cast

import stevedore
from stevedore.exception import NoMatches

from bgmi import namespace
from bgmi.config import cfg
from bgmi.lib.table import STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD, Download, Session
from bgmi.plugin.download import BaseDownloadService
from bgmi.utils import bangumi_save_path, print_error, print_info
from bgmi.website.base import Episode


def get_download_driver(delegate: str) -> BaseDownloadService:
    try:
        return cast(
            BaseDownloadService,
            stevedore.DriverManager(namespace.DOWNLOAD_DELEGATE, name=delegate, invoke_on_load=True).driver,
        )
    except NoMatches:
        print_error(f"can't load download delegate {delegate}")
        raise


def download_prepare(data: List[Episode]) -> None:
    queue = save_to_bangumi_download_queue(data)
    driver = get_download_driver(cfg.download_delegate)
    for download in queue:
        save_path = bangumi_save_path(download.bangumi_name).joinpath(str(download.episode))
        if not save_path.exists():
            os.makedirs(save_path)

        # mark as downloading
        download.status = STATUS_DOWNLOADING
        download.save()
        try:
            driver.add_download(url=download.download, save_path=str(save_path))
            print_info("Add torrent into the download queue, " f"the file will be saved at {save_path}")
        except Exception as e:
            if os.getenv("DEBUG"):  # pragma: no cover
                traceback.print_exc()
                raise e

            print_error(f"Error when downloading {download.title}: {e}", stop=False)
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
        with Session.begin() as session:
            download = Download(
                title=i.title,
                download=i.download,
                bangumi_name=i.name,
                episode=i.episode,
                status=STATUS_NOT_DOWNLOAD,
            )

            session.add(download)

        queue.append(download)

    return queue
