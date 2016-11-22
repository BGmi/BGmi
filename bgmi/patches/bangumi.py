# coding=utf-8
from __future__ import print_function, unicode_literals
import inspect


class Patch(object):
    def patch_bangumi_parser_netoge_no_yome_wa_onnanoko_ja_nai_to_omotta(self, data):
        # patching for 线上游戏的老婆不可能是女生？
        return [i for i in data if '[TSDM&LoveEcho!漫画组]' not in i['title']]

    def patch_www_working(self, data):
        # patching for WWW.WORKING!!
        return [i for i in data if '[WWW.迷糊餐厅!! WWW.WORKING!!][80][BIG5]' not in i['title']]


def main(data):
    patch = Patch()
    func_list = [i for i in dir(patch) if i.startswith('patch_') and inspect.ismethod(getattr(patch, i))]
    for func in func_list:
        data = getattr(patch, func)(data)

    return data
