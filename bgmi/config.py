# coding=utf-8
from __future__ import unicode_literals
import os
import sys


# Setting dmhy url
DMHY_URL = 'http://dmhy.ricterz.me'
FETCH_URL = '{0}/cms/page/name/programme.html'.format(DMHY_URL)
DETAIL_URL = '{0}/topics/list?keyword='.format(DMHY_URL)

IS_PYTHON3 = sys.version_info.major == 3

# Debug Mode
DEBUG = False

# BGmi user path
BGMI_PATH = os.path.join(os.environ.get('HOME', '/tmp'), '.bgmi')
DB_PATH = os.path.join(BGMI_PATH, 'bangumi.db')
BGMI_SAVE_PATH = os.path.join(BGMI_PATH, 'bangumi')

# Xunlei offline download
BGMI_LX_PATH = os.path.join(BGMI_PATH, 'bgmi-lx')

# Download delegate
DOWNLOAD_DELEGATE = 'xunlei'
