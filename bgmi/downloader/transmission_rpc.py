from __future__ import print_function, unicode_literals
import base64
from six import iteritems

from bgmi.downloader.base import BaseDownloadService
from bgmi.config import TRANSMISSION_RPC_PORT, TRANSMISSION_RPC_URL, TRANSMISSION_RPC_USERNAME, TRANSMISSION_RPC_PASSWORD, IS_PYTHON3
from bgmi.utils import print_info, print_warning


if IS_PYTHON3:
    from urllib.request import build_opener
    from urllib.parse import urlparse
else:
    from urllib2 import build_opener
    from urlparse import urlparse


try:
    import transmissionrpc
    from transmissionrpc.utils import make_rpc_name, argument_value_convert

    class PatchClient(transmissionrpc.Client):
        def add_torrent(self, torrent, timeout=None, **kwargs):
            if torrent is None:
                raise ValueError('add_torrent requires data or a URI.')
            torrent_data = None
            parsed_uri = urlparse(torrent)
            if parsed_uri.scheme in ['ftp', 'ftps', 'http', 'https']:
                # there has been some problem with T's built in torrent fetcher,
                # use a python one instead
                opener = build_opener()
                opener.addheaders = [('User-Agent', 'BGmi/Torrent-Downloader')]
                torrent_file = opener.open(torrent)

                torrent_data = torrent_file.read()
                torrent_data = base64.b64encode(torrent_data).decode('utf-8')
            if parsed_uri.scheme in ['file']:
                filepath = torrent
                # uri decoded different on linux / windows ?
                if len(parsed_uri.path) > 0:
                    filepath = parsed_uri.path
                elif len(parsed_uri.netloc) > 0:
                    filepath = parsed_uri.netloc
                torrent_file = open(filepath, 'rb')
                torrent_data = torrent_file.read()
                torrent_data = base64.b64encode(torrent_data).decode('utf-8')
            if not torrent_data:
                if torrent.endswith('.torrent') or torrent.startswith('magnet:'):
                    torrent_data = None
                else:
                    might_be_base64 = False
                    try:
                        # check if this is base64 data
                        if IS_PYTHON3:
                            base64.b64decode(torrent.encode('utf-8'))
                        else:
                            base64.b64decode(torrent)
                        might_be_base64 = True
                    except Exception:
                        pass
                    if might_be_base64:
                        torrent_data = torrent
            args = {}
            if torrent_data:
                args = {'metainfo': torrent_data}
            else:
                args = {'filename': torrent}
            for key, value in iteritems(kwargs):
                argument = make_rpc_name(key)
                (arg, val) = argument_value_convert('torrent-add', argument, value, self.rpc_version)
                args[arg] = val
            return list(self._request('torrent-add', args, timeout=timeout).values())[0]
except ImportError:
    class PatchClient(object):
        pass


class TransmissionRPC(BaseDownloadService):

    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist('')
        super(TransmissionRPC, self).__init__(*args, **kwargs)

    def download(self):
        try:
            import transmissionrpc
            tc = PatchClient(TRANSMISSION_RPC_URL, port=TRANSMISSION_RPC_PORT, user=TRANSMISSION_RPC_USERNAME, password=TRANSMISSION_RPC_PASSWORD)
            try:
                tc.add_torrent(self.torrent, download_dir=self.save_path)
            except UnicodeEncodeError:
                tc.add_torrent(self.torrent, download_dir=self.save_path.encode('utf-8'))

            print_info('Add torrent into the download queue, the file will be saved at {0}'.format(self.save_path))
        except ImportError:
            pass

    def check_delegate_bin_exist(self, path):
        try:
            import transmissionrpc
        except ImportError:
            raise Exception('Please run `pip install transmissionrpc`')

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        print_info('Print download status in database')
        BaseDownloadService.download_status(status=status)
        print('')
        print_info('Print download status in transmission-rpc')
        try:
            import transmissionrpc
            tc = transmissionrpc.Client(TRANSMISSION_RPC_URL, port=TRANSMISSION_RPC_PORT, user=TRANSMISSION_RPC_USERNAME, password=TRANSMISSION_RPC_PASSWORD)
            for torrent in tc.get_torrents():
                print_info('  * {0}: {1}'.format(torrent.status, torrent), indicator=False)
        except ImportError:
            pass

    @staticmethod
    def install():
        print_warning('Please run `pip install transmissionrpc`')
