import os

import stevedore

from bgmi.lib.constants import NameSpace

cls = stevedore.DriverManager(NameSpace.download_delegate, os.environ['DOWNLOADER']).driver


class Obj:
    pass


download_obj = Obj()
download_obj.name = 'name'
download_obj.episode = 5
download_obj.download = (
    'http://releases.ubuntu.com/18.04/'
    'ubuntu-18.04.2-live-server-amd64.iso.torrent'
)
os.makedirs('/home/travis/.bgmi/bangumi/name/5')
cls(download_obj, save_path='/home/travis/.bgmi/bangumi/name/5')
