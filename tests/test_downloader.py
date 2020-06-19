from unittest import mock

from bgmi.downloader.base import BaseDownloadService
from bgmi.main import main


class MockDownloadService(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def download(self):
        pass

    @staticmethod
    def install():
        pass

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        pass


def return_download_class():
    return MockDownloadService


def test_download(clean_bgmi):
    with mock.patch("bgmi.lib.download.get_download_class", return_download_class):
        main("search 海贼王 --download".split())


def test_update(clean_bgmi, bangumi_names):
    with mock.patch("bgmi.lib.download.get_download_class", return_download_class):
        main(["add"] + bangumi_names + ["--episode", "0"])
        main("update -d".split())


# def test_download_with_filter():
#     with mock.patch("bgmi.lib.download.get_download_class", return_download_class):
#         main("")


def test_search_with_filter():
    with mock.patch("bgmi.lib.download.get_download_class", return_download_class):
        main("search 海贼王 --download --regex .*720.*".split())
