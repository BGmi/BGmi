import xmlrpc.client

from bgmi import config
from bgmi.downloader.base import BaseDownloadService
from bgmi.lib.models import STATUS_DOWNLOADED, STATUS_DOWNLOADING, STATUS_NOT_DOWNLOAD
from bgmi.utils import print_error, print_info, print_success, print_warning


class Aria2DownloadRPC(BaseDownloadService):
    old_version = False

    def __init__(self, *args, **kwargs):
        self.server = xmlrpc.client.ServerProxy(config.ARIA2_RPC_URL)
        Aria2DownloadRPC.check_aria2c_version()
        super().__init__(*args, **kwargs)

    def download(self):
        if self.old_version:
            self.server.aria2.addUri([self.torrent], {"dir": self.save_path})
        else:
            self.server.aria2.addUri(
                config.ARIA2_RPC_TOKEN, [self.torrent], {"dir": self.save_path}
            )
        print_info(
            "Add torrent into the download queue, the file will be saved at {}".format(
                self.save_path
            )
        )

    @staticmethod
    def check_aria2c_version():
        url = config.ARIA2_RPC_URL.split("/")
        url[2] = config.ARIA2_RPC_TOKEN + "@" + url[2]
        url = "/".join(url)
        s = xmlrpc.client.ServerProxy(url)
        r = s.aria2.getVersion(config.ARIA2_RPC_TOKEN)
        version = r["version"]
        if version:
            Aria2DownloadRPC.old_version = version < "1.18.4"
        else:
            print_warning("Get aria2c version failed")

    @staticmethod
    def install():
        print_warning("Please install aria2 by yourself")

    def check_download(self, name):
        pass

    @staticmethod
    def download_status(status=None):
        Aria2DownloadRPC.check_aria2c_version()

        print_info("Print download status in database")
        BaseDownloadService.download_status(status=status)
        print()
        print_info("Print download status in aria2c-rpc")
        try:
            server = xmlrpc.client.ServerProxy(config.ARIA2_RPC_URL)
            # self.server.aria2
            status_dict = {
                STATUS_DOWNLOADING: ["tellActive"],
                STATUS_NOT_DOWNLOAD: ["tellWaiting"],
                STATUS_DOWNLOADED: ["tellStopped"],
                None: ["tellStopped", "tellWaiting", "tellActive"],
            }
            for method in status_dict.get(status):
                if method not in ("tellActive",):
                    params = (0, 1000)
                else:
                    params = ()
                if Aria2DownloadRPC.old_version:
                    data = getattr(server.aria2, method)(*params)
                else:
                    data = getattr(server.aria2, method)(
                        config.ARIA2_RPC_TOKEN, *params
                    )

                if data:
                    print_warning(f"RPC {method}:", indicator=False)

                for row in data:
                    print_success("- {}".format(row["dir"]), indicator=False)
                    for file_ in row["files"]:
                        print_info("    * {}".format(file_["path"]), indicator=False)

        except Exception:
            print_error("Cannot connect to aria2-rpc server")
