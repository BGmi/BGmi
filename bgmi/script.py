import datetime
import glob
import imp
import os
import time
import traceback
from typing import List

import stevedore.exception

from bgmi.config import MAX_PAGE, SCRIPT_PATH
from bgmi.lib.download import download_prepare
from bgmi.lib.models import Followed, Scripts
from bgmi.utils import print_info, print_success, print_warning
from bgmi.website import get_all_provider, get_provider


class ScriptRunner:
    _defined = None
    scripts = []
    download_queue = []

    def __new__(cls, *args, **kwargs):
        if cls._defined is None:

            script_files = glob.glob(f'{SCRIPT_PATH}{os.path.sep}*.py')
            for i in script_files:
                try:
                    s = imp.load_source('script', os.path.join(SCRIPT_PATH, i))
                    script_class = s.Script()

                    if cls.check(script_class):
                        cls.scripts.append(script_class)
                        print_info(f'Load script {i} successfully.')

                except SyntaxError:
                    print_warning(f'Load script {i} failed, ignored')
                    if os.getenv('DEBUG_SCRIPT'):  # pragma: no cover
                        traceback.print_exc()
                        # self.scripts = filter(self._check_followed, self.scripts)
                        # self.scripts = filter(self._check_bangumi, self.scripts)

            cls._defined = super().__new__(cls, *args, **kwargs)

        return cls._defined

    @classmethod
    def check(cls, script) -> bool:
        condition = [
            lambda: script.Model().due_date > datetime.datetime.now(),
        ]

        for i in condition:
            try:
                if not i():
                    return False
            except (SyntaxError, TypeError):
                # ignore if error
                if os.getenv('DEBUG_SCRIPT'):  # pragma: no cover
                    traceback.print_exc()

        return True

    def get_model(self, name: str) -> Scripts:
        for script in self.scripts:
            if script.Model.bangumi_name == name:
                return script.Model().obj

    def get_models_dict(self) -> List[dict]:
        return [dict(script.Model()) for script in self.scripts if script.bangumi_name is not None]

    @staticmethod
    def make_dict(script) -> List[dict]:
        return [{
            'name': script.bangumi_name,
            'title': f'[{script.bangumi_name}][{k}]',
            'episode': k,
            'download': v,
        } for k, v in script.get_download_url().items()]

    def run(self, return_=True, download=False) -> List[dict]:
        for script in self.scripts:
            print_info(f'fetching {script.bangumi_name} ...')
            download_item = self.make_dict(script)

            script_obj = script.Model().obj

            if not download_item:
                print_info(f'Got nothing, quit script {script.Model.bangumi_name}.')
                continue

            max_episode = max(download_item, key=lambda d: d['episode'])
            episode = max_episode['episode']
            episode_range = range(script_obj.episode + 1, episode + 1)

            if episode <= script_obj.episode:
                continue

            print_success(f'{script.bangumi_name} updated, episode: {episode}')
            script_obj.episode = episode
            script_obj.status = Followed.STATUS.UPDATED
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
                print_success(f'Start downloading of {script}')
                download_prepare(download_queue)

        return self.download_queue

    def get_download_cover(self) -> List[dict]:
        return [script['cover'] for script in self.get_models_dict()]


class ScriptBase:
    class Model:
        obj = None

        # data
        bangumi_name = None
        cover = None
        update_time = None
        due_date = None

        # source
        source = None

        # fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=MAX_PAGE):
        bangumi_id = None
        subtitle_list = []  # type: list
        max_page = MAX_PAGE

        def __init__(self):
            if self.bangumi_name is not None:
                s, _ = Scripts.get_or_create(
                    bangumi_name=self.bangumi_name,
                    defaults={'episode': 0, 'status': Followed.STATUS.FOLLOWED}
                )
                self.obj = s

        def __iter__(self):
            for i in ('bangumi_name', 'cover', 'update_time'):
                yield (i, getattr(self, i))

            # patch for cal
            yield ('name', self.bangumi_name)
            yield ('status', self.obj.status)
            yield ('updated_time', self.obj.updated_time)
            yield ('subtitle_group', '')
            yield ('episode', self.obj.episode)
            yield ('bangumi_names', [
                self.bangumi_name,
            ])
            yield ('data_source', {})

    @property
    def _data(self) -> dict:
        return {
            'bangumi_id': self.Model.bangumi_id,
            'subtitle_list': self.Model.subtitle_list,
            'max_page': int(self.Model.max_page),
        }

    @property
    def source(self) -> str:
        return self.Model.source

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
        return self.Model.update_time

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
        if self.source is not None:
            try:
                source = get_provider(self.source)
            except stevedore.exception.NoMatches:
                raise Exception(
                    'Script data source is invalid, usable sources: {}'.format(
                        ', '.join(name for name, _ in get_all_provider())
                    )
                )
            ret = {}
            data = source.fetch_episode_of_bangumi(**self._data)
            for i in data:
                if int(i['episode']) not in data:
                    ret[int(i['episode'])] = i['download']
            return ret
        return {}


if __name__ == '__main__':
    runner = ScriptRunner()
    runner.run()
