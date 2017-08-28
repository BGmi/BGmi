# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import imp
import glob
import time

from bgmi.models import Bangumi, Followed, STATUS_UPDATED, STATUS_UPDATING
from bgmi.utils.utils import print_success, print_warning, print_info
from bgmi.config import SCRIPT_PATH, DOWNLOAD_DELEGATE
from bgmi.download import DOWNLOAD_DELEGATE_DICT, download_prepare


class ScriptRunner(object):
    scripts = []
    download_queue = []

    def __init__(self):
        script_files = glob.glob('{}{}*.py'.format(SCRIPT_PATH, os.path.sep))
        for i in script_files:
            try:
                s = imp.load_source('script', os.path.join(SCRIPT_PATH, i))
                script_class = getattr(s, 'Script')()
                self.scripts.append(script_class)
                print_success('Load script {} successfully.'.format(i))
            except Exception as e:
                print_warning('Load script {} failed, ignored'.format(i))
                if os.getenv('DEBUG'):
                    print(e)

        self.scripts = filter(self._check_followed, self.scripts)
        self.scripts = filter(self._check_delegate, self.scripts)
        self.scripts = filter(self._check_bangumi, self.scripts)

    @staticmethod
    def _check_bangumi(script):
        bangumi_obj = Bangumi(name=script.bangumi_name)
        bangumi_obj.select_obj()
        if script.ignore_if_finished and not bangumi_obj.status == STATUS_UPDATING:
            print_warning('Bangumi finished, ignore script: {}'.format(script.bangumi_name, script))
            return False
        return True

    @staticmethod
    def _check_followed(script):
        followed_obj = Followed(bangumi_name=script.bangumi_name)
        followed_obj.select_obj()
        if not followed_obj:
            print_warning('Invalid bangumi of script: {}, ignored.'.format(script.bangumi_name, script))
            return False
        return True

    @staticmethod
    def _check_delegate(script):
        if script.download_delegate is None:
            script.download_delegate = DOWNLOAD_DELEGATE

        elif script.download_delegate not in DOWNLOAD_DELEGATE_DICT.keys():
            print_warning('Invalid download delegate of script: {}, ignored.'.format(script))
            return False

        return True

    @staticmethod
    def make_dict(script):
        return [{
            'name': script.bangumi_name,
            'title': '[{}][{}]'.format(script.bangumi_name, k),
            'episode': k,
            'download': v
        } for k, v in script.get_download_url().items()]

    def run(self, bangumi_list=None, return_=True, download=False):
        bangumi_list = list(map(lambda b: b['bangumi_name'], bangumi_list))
        for script in self.scripts:
            print_info('fetching {} ...'.format(script.bangumi_name))

            if isinstance(bangumi_list, (list, tuple)):
                if script.bangumi_name not in bangumi_list:
                    break

            followed_obj = Followed(bangumi_name=script.bangumi_name)
            followed_obj.select_obj()

            download_item = self.make_dict(script)

            if not download_item:
                print_info('Got nothing, quit script {}.'.format(script))
                break

            max_episode = max(download_item, key=lambda d: d['episode'])
            episode = max_episode['episode']
            episode_range = range(followed_obj.episode + 1, episode + 1)

            if episode <= followed_obj.episode:
                break

            print_success('{} updated, episode: {}'.format(script.bangumi_name, episode))
            followed_obj.episode = episode
            followed_obj.status = STATUS_UPDATED
            followed_obj.updated_time = int(time.time())
            followed_obj.save()

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
    bangumi_name = None
    download_delegate = None

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