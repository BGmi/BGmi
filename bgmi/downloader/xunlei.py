import os
from tempfile import NamedTemporaryFile

from bgmi.config import BGMI_PATH, TMP_PATH, XUNLEI_LX_PATH
from bgmi.downloader.base import BaseDownloadService
from bgmi.utils import print_info, print_success, print_warning


class XunleiLixianDownload(BaseDownloadService):
    def __init__(self, *args, **kwargs):
        self.check_delegate_bin_exist(XUNLEI_LX_PATH)
        super().__init__(*args, **kwargs)

    def download(self):
        print_warning(
            "XunleiLixian is deprecated, please choose aria2-rpc or transmission-rpc."
        )
        overwrite = "--overwrite" if self.overwrite else ""

        command = [
            XUNLEI_LX_PATH,
            "download",
            "--torrent",
            overwrite,
            f"--output-dir={self.save_path}",
            self.torrent,
            "--verification-code-path={}".format(os.path.join(TMP_PATH, "vcode.jpg")),
        ]

        print_info("Run command {}".format(" ".join(command)))
        print_warning(
            "Verification code path: {}".format(os.path.join(TMP_PATH, "vcode.jpg"))
        )
        self.call(command)

    @staticmethod
    def install():
        # install xunlei-lixian
        import tarfile

        import requests

        print_info(
            "Downloading xunlei-lixian from https://github.com/iambus/xunlei-lixian/"
        )
        r = requests.get(
            "https://github.com/iambus/xunlei-lixian/tarball/master",
            stream=True,
            headers={"Accept-Encoding": ""},
        )
        f = NamedTemporaryFile(delete=False)

        with f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        f.close()
        print_success(f"Download successfully, save at {f.name}, extracting ...")
        zip_file = tarfile.open(f.name, "r:gz")
        zip_file.extractall(os.path.join(BGMI_PATH, "tools/xunlei-lixian"))
        dir_name = zip_file.getnames()[0]

        print_info("Create link file ...")

        if not os.path.exists(XUNLEI_LX_PATH):
            os.symlink(
                os.path.join(
                    BGMI_PATH, f"tools/xunlei-lixian/{dir_name}/lixian_cli.py"
                ),
                XUNLEI_LX_PATH,
            )
        else:
            print_warning(f"{XUNLEI_LX_PATH} already exists")

        print_success("All done")
        print_info(
            "Please run command '{} config' to configure your lixian-xunlei "
            "(Notice: only for Thunder VIP)".format(XUNLEI_LX_PATH)
        )
