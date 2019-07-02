import os
from typing import List

import stevedore
import stevedore.exception

from bgmi.config import DOWNLOAD_DELEGATE, SAVE_PATH
from bgmi.downloader.base import AuthError, BaseDownloadService, ConnectError, RequireNotSatisfied
from bgmi.lib import models
from bgmi.lib.constants import NameSpace
from bgmi.lib.db_models import Download
from bgmi.utils import normalize_path, print_error


def get_download_class(rpc_name) -> BaseDownloadService:
    try:
        return stevedore.DriverManager(
            NameSpace.download_delegate,
            rpc_name,
            invoke_on_load=True,
        ).driver
    except stevedore.exception.NoMatches:
        print_error(f'unexpected delegate {rpc_name}')


def download_prepare(name, data: List[models.Episode]):
    queue = save_to_bangumi_download_queue(name, data)
    try:

        download_class = get_download_class(DOWNLOAD_DELEGATE)

    except AuthError:
        return

    except RequireNotSatisfied:
        return

    except ConnectError:
        return

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

            download_class.download(torrent=download.name, save_path=save_path)

            # mark as downloaded
            download.downloaded()

        except Exception as e:  # pylint: disable=W0703
            print_error(f'Error, {e}', exit_=False)

            download.status = Download.STATUS.NOT_DOWNLOAD
            download.save()

            if os.getenv('DEBUG'):  # pragma: no cover
                import traceback

                traceback.print_exc()
                raise e


def save_to_bangumi_download_queue(name, data: List[models.Episode]):
    queue = []
    for i in data:
        download, _ = Download.get_or_create(
            title=i.title,
            download=i.download,
            name=name,
            episode=i.episode,
            status=Download.STATUS.NOT_DOWNLOAD
        )

        queue.append(download)

    return queue
