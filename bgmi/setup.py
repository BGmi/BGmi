# coding=utf-8
import os
import zipfile
from io import BytesIO
from shutil import move

import requests

from bgmi.config import BGMI_SAVE_PATH, BGMI_ADMIN_PATH, BGMI_PATH, DOWNLOAD_DELEGATE, BGMI_TMP_PATH, SCRIPT_PATH
from bgmi.download import get_download_class
from bgmi.utils import print_success, print_warning, print_info, print_error


def unzip(zip_name, unzip_dir):
    """ http://www.jianshu.com/p/27c68168f153 """
    if not os.path.exists(unzip_dir):
        os.mkdir(unzip_dir)
    zipfile_obj = zipfile.ZipFile(zip_name)
    for file_name in zipfile_obj.namelist():
        file_name = file_name.replace('\\', '/')
        if file_name.endswith('/'):
            os.mkdir(os.path.join(unzip_dir, file_name))
        else:
            ext_filename = os.path.join(unzip_dir, file_name)
            ext_file_dir = os.path.dirname(ext_filename)
            if not os.path.exists(ext_file_dir):
                os.mkdir(ext_file_dir)
            data = zipfile_obj.read(file_name)
            with open(ext_filename, 'wb') as f:
                f.write(data)
    zipfile_obj.close()


def install_web_admin():
    print_info('Installing web admin')

    try:
        r = requests.get('https://cdn.rawgit.com/Trim21/bgmi-admin/dist/dist.zip?raw=true')
    except requests.exceptions.ConnectionError:
        print_warning('failed to download web admin')
        return

    admin_zip = BytesIO(r.content)
    unzip(admin_zip, BGMI_ADMIN_PATH)
    for file in os.listdir(os.path.join(BGMI_ADMIN_PATH, 'dist')):
        move(os.path.join(BGMI_ADMIN_PATH, 'dist', file), os.path.join(BGMI_ADMIN_PATH, file))
    os.removedirs(os.path.join(BGMI_ADMIN_PATH, 'dist'))
    print_success('web admin page installed successfully')


def install_crontab():
    print_info('Installing crontab job')
    path = os.path.join(os.path.dirname(__file__), 'crontab.sh')
    os.system('sh \'%s\'' % path)


def create_dir():
    if not os.environ.get('HOME', ''):
        print_warning('$HOME not set, use \'/tmp/\'')

    tools_path = os.path.join(BGMI_PATH, 'tools')
    # bgmi home dir
    path_to_create = (BGMI_PATH, BGMI_SAVE_PATH, BGMI_TMP_PATH, SCRIPT_PATH, tools_path, BGMI_ADMIN_PATH)

    try:
        for path in path_to_create:
            if not os.path.exists(path):
                print_success('%s created successfully' % path)
                os.mkdir(path)
            else:
                print_warning('%s already exists' % path)
    except OSError as e:
        print_error('Error: {0}'.format(str(e)))


def install():
    get_download_class(DOWNLOAD_DELEGATE, instance=False).install()
