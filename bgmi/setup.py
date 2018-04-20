# coding=utf-8
import os
from shutil import copy
from bgmi import __version__
from bgmi.config import (IS_WINDOWS, BGMI_PATH, DOWNLOAD_DELEGATE,
                         SAVE_PATH, FRONT_STATIC_PATH, TMP_PATH, SCRIPT_PATH, TOOLS_PATH)
from bgmi.lib.download import get_download_class
from bgmi.utils import print_success, print_warning, print_info, print_error


def install_crontab():
    print_info('Installing crontab job')
    if IS_WINDOWS:
        copy(os.path.join(os.path.dirname(__file__), 'others/cron.vbs'), BGMI_PATH)
        os.system('schtasks /Create /SC HOURLY /TN "bgmi updater" /TR "{}"  /IT /F'.format(
            os.path.join(BGMI_PATH, 'cron.vbs')))
    else:
        path = os.path.join(os.path.dirname(__file__), 'others/crontab.sh')
        os.system("bash '%s'" % path)


def create_dir():
    path_to_create = (BGMI_PATH, SAVE_PATH, TMP_PATH,
                      SCRIPT_PATH, TOOLS_PATH, FRONT_STATIC_PATH)

    if not os.environ.get('HOME', os.environ.get('USERPROFILE', '')):
        print_warning('$HOME not set, use \'/tmp/\'')

    # bgmi home dir
    try:
        for path in path_to_create:
            if not os.path.exists(path):
                os.makedirs(path)
                print_success('%s created successfully' % path)
        OLD = os.path.join(BGMI_PATH, 'old')
        # create OLD if not exist oninstall
        if not os.path.exists(OLD):
            with open(OLD, 'w') as f:
                f.write(__version__)
    except OSError as e:
        print_error('Error: {0}'.format(str(e)))


def install():
    get_download_class(DOWNLOAD_DELEGATE, instance=False).install()
