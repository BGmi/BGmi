# coding=utf-8
from __future__ import print_function, unicode_literals

patch_dict = {
    '魔法少女☆伊莉雅 3rei!!': 'Liner%7C莉雅%203re',
    '槍彈辯駁3': '論破3',
    '槍彈辯駁3未來篇': '論破3%20未来',
    '槍彈辯駁3絕望篇': '論破3%20绝望',
    '食戟之靈 貳之皿': '食戟%20皿',
    'Show by ROCK!!': 'SHOW+BY+ROCK+第二季',
    '我老婆是學生會長!+!': '老婆%20生會',
}


def main(keyword, origin):
    if keyword in patch_dict:
        return patch_dict[keyword]
    return origin
