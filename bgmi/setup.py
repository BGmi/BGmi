# coding=utf-8
import os
import tarfile
from tempfile import NamedTemporaryFile
from bgmi.utils import print_success, print_warning, print_info
from bgmi.config import IS_PYTHON3, BGMI_LX_PATH, BGMI_SAVE_PATH, BGMI_PATH

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

    tools_path = os.path.join(BGMI_PATH, 'tools')
    # bgmi home dir
    path_to_create = (BGMI_PATH, BGMI_SAVE_PATH, tools_path)

    for path in path_to_create:
        if not os.path.exists(path):
            print_success('%s created successfully' % path)
            os.mkdir(path)
        else:
            print_warning('%s are already exist' % path)


def install_xunlei_lixian():
    import requests
    print_info('Downloading xunlei-lixian from https://github.com/iambus/xunlei-lixian/')
    r = requests.get('https://github.com/iambus/xunlei-lixian/tarball/master', stream=True,
                     headers={'Accept-Encoding': ''})
    f = NamedTemporaryFile(delete=False)
    create_dir()

    with f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    f.close()
    print_success('Download successfully, save at %s, extracting ...' % f.name)
    zip_file = tarfile.open(f.name, 'r:gz')
    zip_file.extractall(os.path.join(BGMI_PATH, 'tools/xunlei-lixian'))
    dir_name = zip_file.getnames()[0]

    print_info('Create link file ...')

    if not os.path.exists(BGMI_LX_PATH):
        os.symlink(os.path.join(BGMI_PATH, 'tools/xunlei-lixian/%s/lixian_cli.py' % dir_name),
                   BGMI_LX_PATH)
    else:
        print_warning('%s already exists' % BGMI_LX_PATH)

    print_success('All done')
    print_info('Please run command \'%s config\' to configure your lixian-xunlei (Notice: only for Thunder VIP)'
               % BGMI_LX_PATH)


if __name__ == '__main__':
    install_xunlei_lixian()
