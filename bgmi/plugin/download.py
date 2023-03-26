import abc
from enum import Enum


class DownloadStatus(Enum):
    not_downloading = 0
    downloading = 1
    done = 2
    error = 3
    not_found = 4


class BaseDownloadService(metaclass=abc.ABCMeta):
    """Wrapped RPC client."""

    @abc.abstractmethod
    def add_download(self, url: str, save_path: str) -> str:
        """download episode

        :param url: torrent url or magnet link
        :param save_path: should passed to downloader, episode info has been joined.
        :return: task id
        """

    @staticmethod
    @abc.abstractmethod
    def check_config() -> None:
        """check current config, don't try to connect."""

    @abc.abstractmethod
    def get_status(self, id: str) -> DownloadStatus:
        """status of downloading task"""


class MissingDependencyError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()


class RpcError(Exception):
    pass
