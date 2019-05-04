from collections import defaultdict

import peewee as pw
from playhouse.shortcuts import model_to_dict

from bgmi.lib.models._tables import (
    Bangumi, BangumiItem, BangumiLink, Download, Followed, Scripts, Subtitle
)

from ._db import db
from ._kv import get_kv_storage

DoesNotExist = pw.DoesNotExist


def order_by_weekday(data, obj=False) -> defaultdict:
    weekly_list = defaultdict(list)
    for bangumi_item in data:
        if obj:
            weekly_list[bangumi_item.update_time.lower()].append(bangumi_item)
        else:
            weekly_list[bangumi_item['update_time'].lower()].append(bangumi_item)
    return weekly_list


def get_updating_bangumi_with_data_source(status=None, order=True):
    common_cond = ((Bangumi.status == Bangumi.STATUS.UPDATING) & (Bangumi.has_data_source == 1))

    query = Bangumi.select(Followed.status, Followed.episode, Bangumi) \
        .join(Followed, pw.JOIN.LEFT_OUTER, on=(Bangumi.id == Followed.bangumi_id))

    if status is None:
        data = query.where(common_cond)
    else:
        data = query.where(common_cond & (Followed.status == status))

    data = data.dicts()

    if order:
        weekly_list = order_by_weekday(data)
    else:
        weekly_list = list(data)

    return weekly_list


def get_followed_bangumi():
    common_cond = ((Bangumi.status == Bangumi.STATUS.UPDATING) & (Bangumi.has_data_source == 1))
    data = Followed.select(Followed, Bangumi, Bangumi.id) \
        .join(Bangumi, pw.JOIN.LEFT_OUTER, on=(Bangumi.id == Followed.bangumi_id))\
        .where(common_cond).dicts()
    weekly_list = order_by_weekday(data)
    return weekly_list


def recreate_source_relatively_table():
    table_to_drop = [Bangumi, Subtitle, Followed, Download]
    for table in table_to_drop:
        table.delete().execute()
    return True


bangumi_links = BangumiLink.get_all()

combined_bangumi = bangumi_links[BangumiLink.STATUS.link]
uncombined_bangumi = bangumi_links[BangumiLink.STATUS.unlink]

__all__ = [
    'db',
    'get_kv_storage',
    'combined_bangumi',
    'uncombined_bangumi',
    'BangumiItem',
    'Bangumi',
    'Followed',
    'Download',
    'Scripts',
    'Subtitle',
    'BangumiLink',  # tables
    'DoesNotExist',
    'get_updating_bangumi_with_data_source',
    'model_to_dict',
]
if __name__ == '__main__':  # pragma:no cover
    from pprint import pprint

    dd = BangumiItem(name='233')
    pprint(dd)
