# coding: utf-8
from __future__ import unicode_literals, print_function
import requests
import re
from bgmi import __version__
from bgmi.utils.utils import print_info, print_success, print_error
from bgmi.models import DB


UPGRADE_URL = 'http://bgmi.ricterz.me/versions/'
MATCH_VERSION = re.compile('<a href="[0-9_].+?/">([0-9_].+?)/</a>')


def upgrade():
    print_info('Fetch versions ...')
    data = requests.get(UPGRADE_URL).content
    versions = list(filter(lambda x: x > __version__, MATCH_VERSION.findall(data)))
    for version in versions:
        upgrade_info = requests.get('%s%s/upgrade.json' % (UPGRADE_URL, version)).json()
        print_info('Upgrade to version %s' % version)
        if 'sql' in upgrade_info:
            try:
                print_success('Run SQL: %s' % upgrade_info['sql'])
                DB.execute(upgrade_info['sql'])
            except Exception, e:
                print_error('Error: %s' % str(e), exit_=False)
