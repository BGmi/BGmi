import os

from bgmi import __version__
from bgmi.config import (
    BGMI_PATH, DOWNLOAD_DELEGATE, FRONT_STATIC_PATH, IS_WINDOWS, SAVE_PATH, SCRIPT_PATH, TMP_PATH,
    TOOLS_PATH
)
from bgmi.lib import constants
from bgmi.lib.download import get_download_class
from bgmi.lib.models import get_kv_storage
from bgmi.utils import exec_command, print_error, print_info, print_success, print_warning


def install_crontab():
    print_info('Installing crontab job')
    if IS_WINDOWS:
        base = os.path.join(os.path.dirname(__file__), 'others\\windows\\cron')
        exec_command(
            'SCHTASKS /Create /TN "bgmi calendar updater" /SC HOURLY /MO 2 '
            '/TR "{tr}" /F'.format(tr=os.path.join(base, 'cal.vbs'))
        )

        exec_command(
            'SCHTASKS /Create /TN "bgmi bangumi updater" /SC HOURLY /MO 12 '
            '/TR "{tr}" /F'.format(tr=os.path.join(base, 'update.vbs'))
        )
    else:
        path = os.path.join(os.path.dirname(__file__), 'others/crontab.sh')
        exec_command("bash '%s'" % path)


def create_dir():
    path_to_create = (BGMI_PATH, SAVE_PATH, TMP_PATH, SCRIPT_PATH, TOOLS_PATH, FRONT_STATIC_PATH)

    if not os.environ.get('HOME', os.environ.get('USERPROFILE', None)):
        print_warning('$HOME and $BGMI_PATH not set, use a tmp dir ' + BGMI_PATH)

    # bgmi home dir
    try:
        for path in path_to_create:
            if not os.path.exists(path):
                os.makedirs(path)
                print_success('%s created successfully' % path)
        if constants.kv.OLD_VERSION not in get_kv_storage():
            get_kv_storage()[constants.kv.OLD_VERSION] = __version__
    except OSError as e:
        print_error('Error: {}'.format(str(e)))


def install():
    get_download_class(DOWNLOAD_DELEGATE, instance=False).install()
