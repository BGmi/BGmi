# coding=utf-8
from __future__ import print_function, unicode_literals

from bgmi.config import DATA_SOURCE
from bgmi.website import bangumi_moe, mikan


DATA_SOURCE_MAP = {
    'mikan_project': mikan.Mikanani,
    'bangumi_moe': bangumi_moe.BangumiMoe
}


website = DATA_SOURCE_MAP.get(DATA_SOURCE)()
