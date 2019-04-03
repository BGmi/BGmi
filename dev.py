# pragma: no cover, noqa: pylint: diable=all
# monkey patch for dev
import os
from pprint import pprint as print
# use this to cache http data
# https://github.com/active-video/caching-proxy


def replace_url(url):
    if url.startswith('https://'):
        url = url.replace('https://', 'http://localhost:8092/https/')
    elif url.startswith('http://'):
        url = url.replace('http://', 'http://localhost:8092/http/')
    return url


from copy import deepcopy
from requests import Session

origin_request = deepcopy(Session.request)


def req(self, method, url, **kwargs):
    if os.environ.get('BGMI_SHOW_ALL_NETWORK_REQUEST'):
        print(url)
    url = replace_url(url)
    # traceback.print_stack(limit=8)
    return origin_request(self, method, url, **kwargs)


Session.request = req

os.environ.update({
    'BGMI_PATH': os.path.join(os.path.expanduser('~'), 'proj', 'tmp'),
    'BANGUMI_1': '名侦探柯南',
    'BANGUMI_2': '刃牙',
    'BANGUMI_3': '海贼王',
    # "DEBUG": "1",
    'DEV': '1',
})
# monkey patch end

from bgmi import main, website  # noqa
from bgmi.lib import models
from bgmi.lib.models import BangumiItem
import peewee as pw

main.main('cal --force-update'.split(' '))
