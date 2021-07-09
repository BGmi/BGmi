import abc

from bgmi.plugin.status import DownloadStatus


class BaseDownloadService(metaclass=abc.ABCMeta):
    """Wrapped RPC client."""

    @abc.abstractmethod
    def __init__(self):
        """Initialize rpc client here."""

    @abc.abstractmethod
    def add_download(self, url: str, save_path: str, overwrite: bool = False) -> str:
        """download episode

        :param url: torrent url or magnet link
        :param save_path: should passed to downloader, episode info has been joined.
        :param overwrite: if downloader could overwrite file content.
        :return: task id
        """

    @staticmethod
    @abc.abstractmethod
    def check_dep():
        """check dependencies like rpc library

        :raises MissingDependencyError:
        """

    @abc.abstractmethod
    def get_status(self, id: str) -> DownloadStatus:
        """status of downloading task"""


class MissingDependencyError(Exception):
    def __init__(self, message):
        self.message = message
