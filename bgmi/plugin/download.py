import abc
from enum import Enum
from typing import List


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

    @abc.abstractmethod
    def get_status(self, id: str) -> DownloadStatus:
        """status of downloading task"""

    @abc.abstractmethod
    def get_files(self, id: str) -> List[str]:
        """Get list of file paths for a completed task.

        :param id: task id returned by add_download
        :return: list of file paths (absolute or relative to save_path)
        """

    def remove_download(self, id: str) -> None:
        """Remove a completed task from the downloader. Default no-op for compatibility."""


class MissingDependencyError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()


class RpcError(Exception):
    pass
