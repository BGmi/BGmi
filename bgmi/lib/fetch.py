from typing import Dict, Type

from bgmi.config import cfg
from bgmi.utils import print_error
from bgmi.website import bangumi_moe, base, mikan, share_dmhy

DATA_SOURCE_MAP: Dict[str, Type[base.BaseWebsite]] = {
    "mikan_project": mikan.Mikanani,
    "bangumi_moe": bangumi_moe.BangumiMoe,
    "dmhy": share_dmhy.DmhySource,
}

try:
    website = DATA_SOURCE_MAP[cfg.data_source]()
except KeyError:
    print_error(f'date source "{cfg.data_source}" in config is wrong, please edit it manually')
