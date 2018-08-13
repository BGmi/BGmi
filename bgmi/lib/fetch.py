# coding=utf-8

from bgmi.utils import print_error
from bgmi.website import bangumi_moe, mikan, share_dmhy

DATA_SOURCE_MAP = {
    'mikan_project': mikan.Mikanani,
    'bangumi_moe': bangumi_moe.BangumiMoe,
    'dmhy': share_dmhy.DmhySource,
}

website = bangumi_moe.BangumiMoe()
