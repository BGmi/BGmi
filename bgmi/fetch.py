# coding=utf-8
from __future__ import print_function, unicode_literals

from bgmi.config import WEBSITE_NAME

from bgmi.website.bangumimoe import BangumiMoe
from bgmi.website.mikan import Mikanani

if WEBSITE_NAME == 'mikan_project':
    website = Mikanani()
else:
    website = BangumiMoe()
