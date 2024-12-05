import datetime
import glob
import os
import time
import traceback
import types
from importlib.machinery import SourceFileLoader
from operator import itemgetter
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple, runtime_checkable

from bgmi.config import cfg
from bgmi.lib.download import Episode, download_prepare
from bgmi.lib.fetch import DATA_SOURCE_MAP
from bgmi.lib.models import STATUS_FOLLOWED, STATUS_UPDATED, Scripts
from bgmi.utils import print_info, print_success, print_warning
from bgmi.website.model import WebsiteBangumi


class ScriptRunner:
    _defined = None
    scripts = []  # type: List[ScriptBase]
    download_queue = []  # type: List[Episode]

    def __new__(cls, *args, **kwargs):  # type: ignore
        if cls._defined is None:
            script_files = glob.glob(f"{cfg.script_path}{os.path.sep}*.py")
            for i in script_files:
                try:
                    loader = SourceFileLoader("script", os.path.join(cfg.script_path, i))
                    mod = types.ModuleType(loader.name)
                    loader.exec_module(mod)
                    script_class = mod.Script()  # pylint:disable=no-member
                except Exception:
                    print_warning(f"Load script {i} failed, ignored")
                    if os.getenv("DEBUG_SCRIPT"):  # pragma: no cover
                        traceback.print_exc()
                    continue
                cls.check(script_class, i)

            cls._defined = super().__new__(cls, *args, **kwargs)

        return cls._defined

    @classmethod
    def check(cls, script: "ScriptBase", fs: str) -> None:
        model = script.Model()
        if model.due_date and model.due_date < datetime.datetime.now():
            print(f"Skip load {fs} because it has reach its due_date")
            return

        cls.scripts.append(script)
        print_info(f"Load script {fs} successfully.")

    def get_model(self, name: str) -> Optional[Scripts]:
        for script in self.scripts:
            if script.Model.bangumi_name == name:
                return script.Model().obj
        return None

    def get_models(self) -> List[WebsiteBangumi]:
        m = []
        for s in self.scripts:
            model = s.Model()
            m.append(
                WebsiteBangumi(
                    name=model.bangumi_name,
                    update_time=model.update_time,
                    keyword=model.bangumi_name,
                    cover=model.cover,
                )
            )
        return m

    def get_models_dict(self) -> List[dict]:
        return [dict(script.Model()) for script in self.scripts if script.bangumi_name is not None]

    @staticmethod
    def make_dict(script: "ScriptBase") -> List[Dict[str, Any]]:
        return [
            {
                "name": script.bangumi_name,
                "title": f"[{script.bangumi_name}][{k}]",
                "episode": k,
                "download": v,
            }
            for k, v in script.get_download_url().items()
        ]

    def run(self, return_: bool = True, download: bool = False) -> List[Episode]:
        for script in self.scripts:
            print_info(f"fetching {script.bangumi_name} ...")
            download_item = self.make_dict(script)

            script_obj = script.Model().obj

            if not download_item:
                print_info(f"Got nothing, quit script {script}.")
                continue

            max_episode = max(download_item, key=itemgetter("episode"))
            episode = max_episode["episode"]
            episode_range = range(script_obj.episode + 1, episode + 1)

            if episode <= script_obj.episode:
                continue

            download_queue = []
            for i in episode_range:
                for e in download_item:
                    if i == e["episode"]:
                        download_queue.append(e)

            print_success(f"{script.bangumi_name} updated, episode: {episode}")
            script_obj.episode = episode
            script_obj.status = STATUS_UPDATED
            script_obj.updated_time = int(time.time())
            script_obj.save()

            if return_:
                self.download_queue.extend(Episode(**x) for x in download_queue)
                continue

            if download:
                print_success(f"Start downloading of {script}")
                download_prepare([Episode(**x) for x in download_queue])

        return self.download_queue

    def get_download_cover(self) -> List[str]:
        return [script["cover"] for script in self.get_models_dict()]


class ScriptBase:
    class Model:
        obj = None  # type: Scripts

        # data
        bangumi_name = None
        cover = ""
        update_time = "Unknown"
        due_date: Optional[datetime.datetime] = None

        # source
        source = None

        bangumi_id = None
        subtitle_list = []  # type: list
        max_page = cfg.max_path

        def __init__(self) -> None:
            if self.bangumi_name is not None:
                s, _ = Scripts.get_or_create(
                    bangumi_name=self.bangumi_name,
                    defaults={"episode": 0, "status": STATUS_FOLLOWED},
                )  # type: Scripts, bool
                self.obj = s

        def __iter__(self) -> Iterator[Tuple[str, Any]]:
            for i in ("bangumi_name", "cover", "update_time"):
                yield i, getattr(self, i)

            # patch for cal
            yield "name", self.bangumi_name
            yield "status", self.obj.status
            yield "updated_time", self.obj.updated_time
            yield "subtitle_group", ""
            yield "episode", self.obj.episode

    @property
    def _data(self) -> dict:
        return {
            "bangumi_id": self.Model.bangumi_id,
            "subtitle_list": self.Model.subtitle_list,
            "max_page": int(self.Model.max_page),
        }

    @property
    def source(self) -> Optional[str]:
        return self.Model.source

    @property
    def name(self) -> Optional[str]:
        return self.Model.bangumi_name

    @property
    def bangumi_name(self) -> Optional[str]:
        return self.Model.bangumi_name

    @property
    def cover(self) -> Optional[str]:
        return self.Model.cover

    @property
    def updated_time(self) -> str:
        return self.Model.update_time

    def get_download_url(self) -> Dict[int, str]:
        """Get the download url, and return a dict of episode and the url.
        Download url also can be magnet link.
        For example:

        ... code-block:: python

            {
                1: 'https://example.com/Bangumi/1/1.mp4'
                2: 'https://example.com/Bangumi/1/2.mp4'
                3: 'https://example.com/Bangumi/1/3.mp4'
            }

        The keys `1`, `2`, `3` is the episode, the value is the url of bangumi.
        :return: dict
        """
        if self.source is not None:
            try:
                source = DATA_SOURCE_MAP[self.source]()
            except KeyError:
                raise ValueError(
                    "Script data source is invalid, usable sources: {}".format(", ".join(DATA_SOURCE_MAP.keys()))
                )
            ret = {}
            data = source.fetch_episode_of_bangumi(**self._data)
            for i in data:
                if int(i.episode) not in data:
                    ret[int(i.episode)] = i.download
            return ret
        else:
            return {}


class HookRunner:
    hook_script = None  # type: Optional[List[HookBase]]

    def __init__(self) -> None:
        if HookRunner.hook_script is None:
            HookRunner.hook_script = []
            hook_files = glob.glob(f"{cfg.hook_path}{os.path.sep}*.py")

            for i in hook_files:
                try:
                    loader = SourceFileLoader("hook", os.path.join(cfg.hook_path, i))
                    mod = types.ModuleType(loader.name)
                    loader.exec_module(mod)

                    for attribute_name in dir(mod):
                        attribute = getattr(mod, attribute_name)
                        if (
                            isinstance(attribute, type)
                            and issubclass(attribute, HookBase)
                            and attribute is not HookBase
                        ):
                            HookRunner.hook_script.append(attribute())

                except Exception:
                    print_warning(f"Load hook {i} failed, ignored")
                    if os.getenv("DEBUG_SCRIPT"):  # pragma: no cover
                        traceback.print_exc()
                    continue

    def pre_add_download(self) -> None:
        assert self.hook_script is not None
        for script in self.hook_script:
            script.pre_add_download()

    def post_add_download(self, download_queue: Optional[List[object]], redownload_queue: Optional[List[object]]) -> None:
        assert self.hook_script is not None
        for script in self.hook_script:
            script.post_add_download(download_queue=download_queue, redownload_queue=redownload_queue)


@runtime_checkable
class HookBase(Protocol):
    def __init__(self) -> None:
        pass

    def pre_add_download(self, *args: Any, **kwargs: Any) -> None:
        pass

    def post_add_download(self, *args: Any, **kwargs: Any) -> None:
        pass


if __name__ == "__main__":
    runner = ScriptRunner()
    runner.run()

    runner2 = HookRunner()
    runner2.post_add_download(None, None)
