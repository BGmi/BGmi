# coding=utf-8
import os

from bgmi.config import IS_PYTHON3, BGMI_SAVE_PATH, BGMI_PATH, DOWNLOAD_DELEGATE, BGMI_TMP_PATH
from bgmi.download import get_download_class
from bgmi.utils.utils import print_success, print_warning, print_info, print_error


def install_crontab():
    print_info('Installing crontab job')
    path = os.path.join(os.path.dirname(__file__), 'crontab.sh')
    os.system('sh \'%s\'' % path)


def create_dir():
    if not os.environ.get('HOME', ''):
        print_warning('$HOME not set, use \'/tmp/\'')

    tools_path = os.path.join(BGMI_PATH, 'tools')
    # bgmi home dir
    path_to_create = (BGMI_PATH, BGMI_SAVE_PATH, BGMI_TMP_PATH, tools_path)

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
