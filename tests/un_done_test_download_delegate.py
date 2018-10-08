# -*- coding: utf-8 -*-

import os
import unittest

# from bgmi.lib.fetch import website
from bgmi.website import DATA_SOURCE_MAP
from bgmi.website.base import BaseWebsite
import bgmi.website
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmissionRpc import TransmissionRPC
from bgmi.downloader.base import BaseDownloadService
from bgmi.lib.models import Download


class BasicT:
    download_obj = Download(
        name='test_bangumi_name',
        title='test_bangumi_title',
        episode=2,
        download='magnet:?xt=urn:btih:qwerty',
        status=0,
    )
    save_path = './tmp/'
    cls = BaseDownloadService
    instance = BaseDownloadService(download_obj, save_path, True)

    def test_init(self):
        pass

    def test_install(self):
        pass

    def test_download(self):
        pass

    def test_check_path(self):
        pass

    def test_check_delegate_bin_exist(self, path):
        pass

    def test_check_download(self, ):
        pass

    def test_download_status(self):
        pass
    # @staticmethod
    # def setUpClass():
    #     setup()
    #     recreate_source_relatively_table()


class MikanProjectTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'
    w = bgmi.website.Mikanani()


class DMHYTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名偵探柯南'
    bangumi_name_2 = '海賊王'
    w = bgmi.website.DmhySource()


class BangumiMoeTest(BasicT, unittest.TestCase):
    bangumi_name_1 = '名侦探柯南'
    bangumi_name_2 = '海贼王'
    w = bgmi.website.BangumiMoe()
