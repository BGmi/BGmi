from bgmi.lib.models import Bangumi, BangumiItem

print('bgm.tv', 'bangumi_moe', 'mikan', 'dmhy', sep='|')


def get_name(bangumi, data_source):
    return bangumi['data_source'].get(data_source, BangumiItem(name='')).name


for bangumi in Bangumi.get_updating_bangumi(order=False):
    print(bangumi['name'],
          get_name(bangumi, 'bangumi_moe'),
          get_name(bangumi, 'mikan_project'),
          get_name(bangumi, 'dmhy'), sep='|')
