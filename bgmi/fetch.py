# coding=utf-8
from __future__ import print_function, unicode_literals

from bgmi.config import DATA_SOURCE

from bgmi.website.bangumimoe import BangumiMoe
from bgmi.website.mikan import Mikanani

if DATA_SOURCE == 'mikan_project':
    website = Mikanani()
else:
    website = BangumiMoe()
