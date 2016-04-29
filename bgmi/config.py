# coding=utf-8
import os
import sys
FETCH_URL = 'http://dmhy.ricter.me/cms/page/name/programme.html'
DETAIL_URL = 'http://dmhy.ricter.me/topics/list?keyword='
IS_PYTHON3 = sys.version_info.major == 3
DEBUG = False

BGMI_PATH = os.path.join(os.environ.get('HOME', '/tmp'), '.bgmi')
DB_PATH = os.path.join(BGMI_PATH, 'bangumi.db')
