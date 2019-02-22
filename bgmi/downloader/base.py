# coding=utf-8
import os
from abc import abstractmethod, ABC

from bgmi.lib.models import STATUS_DOWNLOADED, STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING, Download
from bgmi.utils import print_warning, print_info, print_success


class BaseDownloadService(ABC):
    def __init__(self, download_obj, save_path, overwrite=True):
        self.name = download_obj.name
        self.torrent = download_obj.download
        self.overwrite = overwrite
        self.save_path = save_path
        self.episode = download_obj.episode
        self.return_code = 0

    @abstractmethod
    def download(self):
        # download
        raise NotImplementedError

    @staticmethod
    def install():
        # install requirement
        raise NotImplementedError

    def check_path(self):
        if not os.path.exists(self.save_path):
            print_warning('Create dir {0}'.format(self.save_path))
            os.makedirs(self.save_path)

    @abstractmethod
    def check_delegate_bin_exist(self):
        raise NotImplementedError

    def check_download(self, name):
        if not os.path.exists(self.save_path) or self.return_code != 0:
            raise Exception('It seems the bangumi {0} not be downloaded'.format(name))

    @staticmethod
    def download_status(status=None):
        last_status = -1
        for download_data in Download.get_all_downloads(status=status):
            latest_status = download_data['status']
            name = '  {0}. <{1}: {2}>'.format(download_data['id'], download_data['name'],
                                              download_data['episode'])
            if latest_status != last_status:
                if latest_status == STATUS_DOWNLOADING:
                    print('Downloading items:')
                elif latest_status == STATUS_NOT_DOWNLOAD:
                    print('Not downloaded items:')
                elif latest_status == STATUS_DOWNLOADED:
                    print('Downloaded items:')

            if download_data['status'] == STATUS_NOT_DOWNLOAD:
                print_info(name, indicator=False)
            elif download_data['status'] == STATUS_DOWNLOADING:
                print_warning(name, indicator=False)
            elif download_data['status'] == STATUS_DOWNLOADED:
                print_success(name, indicator=False)
            last_status = download_data['status']
