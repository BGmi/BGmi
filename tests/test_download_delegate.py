import unittest
from unittest.mock import MagicMock, patch

import bgmi.downloader
import bgmi.website
# from bgmi.lib.fetch import website
from bgmi.config import ARIA2_RPC_TOKEN
from bgmi.downloader.aria2_rpc import Aria2DownloadRPC
from bgmi.downloader.base import BaseDownloadService
from bgmi.downloader.deluge import DelugeRPC
from bgmi.downloader.transmissionRpc import TransmissionRPC
from bgmi.lib.models import Download


class Basic:
    class Test(unittest.TestCase):
        save_path = './tmp/'
        download_obj = Download(
            name='test_bangumi_name',
            title='test_bangumi_title',
            episode=2,
            path=save_path,
            download='magnet:?xt=urn:btih:qwerty',
            status=0,
        )
        cls = BaseDownloadService
        overwrite = True
        # instance = BaseDownloadService(download_obj, save_path, overwrite)


class Aria2cTest(Basic.Test, unittest.TestCase):
    cls = Aria2DownloadRPC

    def test_install(self):
        with patch('bgmi.downloader.aria2_rpc.print_warning') as m:
            self.cls.install()
            m.assert_called_once_with('Please install aria2 by yourself')

    def test_init(self):
        self.aria2 = MagicMock()
        self.m = MagicMock(return_value=MagicMock(aria2=self.aria2))
        # self.aria2.getVersion.return_value = {'version': '2.0.1'}
        self.p = patch('bgmi.downloader.aria2_rpc.PatchedServerProxy', self.m)
        self.p.start()

        self.m.return_value.aria2.getVersion.return_value = {'version': '4.0.1'}

        instance = bgmi.downloader.aria2_rpc.Aria2DownloadRPC(
            self.download_obj, self.save_path, self.overwrite
        )
        self.assertFalse(instance.old_version)

        self.m.return_value.aria2.getVersion.return_value = {'version': '1.0.1'}

        instance = bgmi.downloader.aria2_rpc.Aria2DownloadRPC(
            self.download_obj, self.save_path, self.overwrite
        )
        self.assertTrue(instance.old_version)

        self.p.stop()

    def test_download(self):
        self.aria2 = MagicMock()
        self.m = MagicMock(return_value=MagicMock(aria2=self.aria2))
        self.m.return_value.aria2.getVersion.return_value = {'version': '4.0.1'}
        self.p = patch('bgmi.downloader.aria2_rpc.PatchedServerProxy', self.m)
        self.p.start()

        # not old version
        instance = bgmi.downloader.aria2_rpc.Aria2DownloadRPC(
            self.download_obj, self.save_path, self.overwrite
        )
        instance.download()
        self.m.return_value.aria2.addUri.assert_called_once_with(
            ARIA2_RPC_TOKEN, [self.download_obj.download], {'dir': self.save_path}
        )

        self.m.return_value.aria2.addUri.reset_mock()

        # old version
        self.m.return_value.aria2.getVersion.return_value = {'version': '1.0.1'}
        instance = bgmi.downloader.aria2_rpc.Aria2DownloadRPC(
            self.download_obj, self.save_path, self.overwrite
        )
        instance.download()
        self.m.return_value.aria2.addUri.assert_called_once_with([self.download_obj.download],
                                                                 {'dir': self.save_path})
        self.p.stop()


class TransmissionRPCTest(Basic.Test, unittest.TestCase):
    cls = TransmissionRPC

    def test_install(self):
        with patch('bgmi.downloader.transmissionRpc.print_warning') as m:
            self.cls.install()
            m.assert_called_once_with('Please run `pip install transmission-rpc`')

    def test_init(self):
        mock_client = MagicMock()
        with patch('transmission_rpc.Client', MagicMock(return_value=mock_client)):
            rpc = bgmi.downloader.transmissionRpc.TransmissionRPC(
                self.download_obj, self.save_path, self.overwrite
            )
            rpc.download()
            mock_client.add_torrent.assert_called_once_with(
                self.download_obj.download, download_dir=self.save_path
            )


class DelugeRPCTest(Basic.Test, unittest.TestCase):
    cls = DelugeRPC

    def test_init(self):
        with patch('bgmi.downloader.deluge.DelugeRPC._call') as m:
            bgmi.downloader.deluge.DelugeRPC(self.download_obj, self.save_path, self.overwrite)
            m.assert_called_once_with('auth.login', [
                bgmi.config.DELUGE_RPC_PASSWORD,
            ])

    @patch('bgmi.downloader.deluge.DelugeRPC._call')
    def test_download(self, m):
        rpc = bgmi.downloader.deluge.DelugeRPC(self.download_obj, self.save_path, self.overwrite)
        m.reset_mock()
        rpc.torrent = 'https://b/a.torrent'
        rpc.download()
        # m.call_args_list()
        # m.assert_any_call('web.download_torrent_from_url', [
        #     self.download_obj.download,
        # ])
        for called in m.call_args_list:
            args, kwargs = called
            self.assertIn(args[0], ['web.download_torrent_from_url', 'web.add_torrents'])
