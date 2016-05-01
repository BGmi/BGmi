# coding=utf-8
import os
import tarfile
import requests
from tempfile import NamedTemporaryFile
from bgmi.utils import print_success, print_warning, print_info
from bgmi.config import IS_PYTHON3

if not IS_PYTHON3:
    input = raw_input


def install_crontab():
    print_info('Installing crontab job')
    path = os.path.join(os.path.dirname(__file__), '../crontab.sh')
    os.system('sh \'%s\'' % path)


def create_dir():
    home = os.environ.get('HOME', '')
    if not home:
        print_warning('$HOME not set, use \'/tmp/\'')
        home = '/tmp'

    bgmi_path = os.path.join(home, '.bgmi')

    # bgmi home dir
    if not os.path.exists(bgmi_path):
        print_success('%s created successfully' % bgmi_path)
        os.mkdir(bgmi_path)
    else:
        print_warning('%s are already exist' % bgmi_path)

    # tools dir
    if not os.path.exists(os.path.join(bgmi_path, 'tools')):
        os.mkdir(os.path.join(bgmi_path, 'tools'))
    else:
        print_warning('%s already exists' % os.path.join(bgmi_path, 'tools'))

    return bgmi_path


def install_xunlei_lixian():
    print_info('Downloading xunlei-lixian from https://github.com/iambus/xunlei-lixian/')
    r = requests.get('https://github.com/iambus/xunlei-lixian/tarball/master', stream=True,
                     headers={'Accept-Encoding': ''})
    f = NamedTemporaryFile(delete=False)
    bgmi_path = create_dir()
    bgmi_lx_path = os.path.join(bgmi_path, 'bgmi-lx')

    with f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    f.close()
    print_success('Download successfully, save at %s, extracting ...' % f.name)
    zip_file = tarfile.open(f.name, 'r:gz')
    zip_file.extractall(os.path.join(bgmi_path, 'tools/xunlei-lixian'))
    dir_name = zip_file.getnames()[0]

    print_info('Create link file ...')

    if not os.path.exists(bgmi_lx_path):
        os.symlink(os.path.join(bgmi_path, 'tools/xunlei-lixian/%s/lixian_cli.py' % dir_name),
                   bgmi_lx_path)
    else:
        print_warning('%s already exists' % bgmi_lx_path)

    print_success('All done')
    print_info('Please run command \'%s config\' to configure your lixian-xunlei (Notice: only for Thunder VIP)'
               % bgmi_lx_path)


if __name__ == '__main__':
    install_xunlei_lixian()
