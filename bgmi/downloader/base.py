from abc import ABC, abstractmethod

from bgmi.lib.db_models import Download
from bgmi.models.config import Config
from bgmi.utils import print_info, print_success, print_warning


class ConnectError(Exception):
    pass


class AuthError(Exception):
    pass


class RequireNotSatisfied(Exception):
    def __init__(self, message):
        self.message = message


class BaseDownloadService(ABC):
    config: Config
    """
    Raises
    ------
    ConnectError
        Any connection error
    AuthError
        If RPC server require authorization
    """
    def __init__(self, config: Config, *args, **kwargs):
        self.config = config
        self.require()

    @classmethod
    def require(cls):
        """
        Implement this classmethod if your download delegate has some additional requires

        Notes
        -----
            You can also install dependencies here.
            But this method will be called every time bgmi try to download some files.
            So only install dependencies when missing them.

        Raises
        ------
        RequireNotSatisfied
            If some requirements not satisfied. like missing bin or python package.
            Don't raise ImportError, catch it and describe it in message.
        """

    @abstractmethod
    def download(self, torrent: str, save_path: str):
        """

        Parameters
        ----------
        torrent
            magnet link ot url of torrent file
        save_path
            video file save path on

        Raises
        ------
        AuthError
            Auth failure, no auth provided or wrong auth
        ConnectError
            Network unreachable, or timeout

        """

    def download_status(self, status=None):
        last_status = -1
        for download_data in Download.get_all_downloads(status=status):
            latest_status = download_data['status']
            name = '  {}. <{}: {}>'.format(
                download_data['id'], download_data['name'], download_data['episode']
            )
            if latest_status != last_status:
                if latest_status == Download.STATUS.DOWNLOADING:
                    print('Downloading items:')
                elif latest_status == Download.STATUS.NOT_DOWNLOAD:
                    print('Not downloaded items:')
                elif latest_status == Download.STATUS.DOWNLOADED:
                    print('Downloaded items:')

            if download_data['status'] == Download.STATUS.NOT_DOWNLOAD:
                print_info(name, indicator=False)
            elif download_data['status'] == Download.STATUS.DOWNLOADING:
                print_warning(name, indicator=False)
            elif download_data['status'] == Download.STATUS.DOWNLOADED:
                print_success(name, indicator=False)
            last_status = download_data['status']
