# coding=utf-8
from __future__ import print_function, unicode_literals

import re
import os
import imp
import glob
import time
import traceback

from bgmi.models import STATUS_UPDATED, STATUS_FOLLOWED
from bgmi.utils import print_success, print_warning, print_info
from bgmi.config import SCRIPT_PATH
from bgmi.download import download_prepare
from bgmi.models import Script


FETCH_EPISODE_ZH = re.compile("第?\s?(\d{1,3})\s?[話话集]")
FETCH_EPISODE_WITH_BRACKETS = re.compile('[【\[](\d+)\s?(?:END)?[】\]]')
FETCH_EPISODE_ONLY_NUM = re.compile('^([\d]{2,})$')
FETCH_EPISODE_RANGE = re.compile('[\d]{2,}\s?-\s?([\d]{2,})')
FETCH_EPISODE_OVA_OAD = re.compile('([\d]{2,})\s?\((?:OVA|OAD)\)]')
FETCH_EPISODE_WITH_VERSION = re.compile('[【\[](\d+)\s? *v\d(?:END)?[】\]]')
FETCH_EPISODE = (
    FETCH_EPISODE_ZH, FETCH_EPISODE_WITH_BRACKETS, FETCH_EPISODE_ONLY_NUM,
    FETCH_EPISODE_RANGE,
    FETCH_EPISODE_OVA_OAD, FETCH_EPISODE_WITH_VERSION)


def parse_episode(episode_title):
    """
    parse episode from title

    :param episode_title: episode title
    :type episode_title: str
    :return: episode of this title
    :rtype: int
    """

    _ = FETCH_EPISODE_ZH.findall(episode_title)
    if _ and _[0].isdigit():
        return int(_[0])

    _ = FETCH_EPISODE_WITH_BRACKETS.findall(episode_title)
    if _ and _[0].isdigit():
        return int(_[0])

    _ = FETCH_EPISODE_WITH_VERSION.findall(episode_title)
    if _ and _[0].isdigit():
        return int(_[0])

    for split_token in ['【', '[', ' ']:
        for i in episode_title.split(split_token):
            for regexp in FETCH_EPISODE:
                match = regexp.findall(i)
                if match and match[0].isdigit():
                    return int(match[0])
    return 0


class ScriptRunner(object):
    _defined = None
    scripts = []
    download_queue = []

    def __new__(cls, *args, **kwargs):
        if cls._defined is None:

            script_files = glob.glob('{}{}*.py'.format(SCRIPT_PATH, os.path.sep))
            for i in script_files:
                try:
                    s = imp.load_source('script', os.path.join(SCRIPT_PATH, i))
                    script_class = getattr(s, 'Script')()
                    cls.scripts.append(script_class)
                    print_success('Load script {} successfully.'.format(i))
                except:
                    print_warning('Load script {} failed, ignored'.format(i))
                    traceback.print_exc()
                    # self.scripts = filter(self._check_followed, self.scripts)
                    # self.scripts = filter(self._check_bangumi, self.scripts)

            cls._defined = super(ScriptRunner, cls).__new__(cls, *args, **kwargs)

        return cls._defined

    def get_models(self):
        return [dict(script.Model()) for script in self.scripts if script.bangumi_name is not None]

    @staticmethod
    def make_dict(script):
        return [{
            'name': script.bangumi_name,
            'title': '[{}][{}]'.format(script.bangumi_name, k),
            'episode': k,
            'download': v
        } for k, v in script.get_download_url().items()]

    def run(self, return_=True, download=False):
        for script in self.scripts:
            print_info('fetching {} ...'.format(script.bangumi_name))
            download_item = self.make_dict(script)

            script_obj = script.Model().obj

            if not download_item:
                print_info('Got nothing, quit script {}.'.format(script))
                break

            max_episode = max(download_item, key=lambda d: d['episode'])
            episode = max_episode['episode']
            episode_range = range(script_obj.episode + 1, episode + 1)

            if episode <= script_obj.episode:
                break

            print_success('{} updated, episode: {}'.format(script.bangumi_name, episode))
            script_obj.episode = episode
            script_obj.status = STATUS_UPDATED
            script_obj.updated_time = int(time.time())
            script_obj.save()

            download_queue = []
            for i in episode_range:
                for e in download_item:
                    if i == e['episode']:
                        download_queue.append(e)

            if return_:
                self.download_queue.extend(download_queue)
                continue

            if download:
                print_success('Start downloading of {}'.format(script))
                download_prepare(download_queue)

        return self.download_queue


class ScriptBase(object):

    class Model(object):
        obj = None
        bangumi_name = None
        cover = None
        updated_time = None

        def __init__(self):
            if self.bangumi_name is not None:
                s = Script(bangumi_name=self.bangumi_name, episode=0, status=STATUS_FOLLOWED)
                s.select_obj()
                if not s:
                    s.save()
                self.obj = s

        def __iter__(self):
            for i in ('bangumi_name', 'cover', 'updated_time'):
                yield (i, getattr(self, i))

            # patch for cal
            yield ('update_time', self.updated_time)
            yield ('name', self.bangumi_name)
            yield ('status', self.obj['status'])
            yield ('subtitle_group', '')
            yield ('episode', self.obj['episode'])

    @property
    def name(self):
        return self.Model.bangumi_name

    @property
    def bangumi_name(self):
        return self.Model.bangumi_name

    @property
    def cover(self):
        return self.Model.cover

    @property
    def updated_time(self):
        return self.Model.updated_time

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return '<Script of \'{}\'>'.format(self.bangumi_name)

    def get_download_url(self):
        """Get the download url, and return a dict of episode and the url.
        Download url also can be magnet link.
        For example:
        ```
            {
                1: 'http://example.com/Bangumi/1/1.mp4'
                2: 'http://example.com/Bangumi/1/2.mp4'
                3: 'http://example.com/Bangumi/1/3.mp4'
            }
        ```
        The keys `1`, `2`, `3` is the episode, the value is the url of bangumi.
        :return: dict
        """
        return {}


if __name__ == '__main__':
    runner = ScriptRunner()
    runner.run()
