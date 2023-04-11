import datetime
import glob
import os
import traceback
import types
from importlib.machinery import SourceFileLoader
from typing import Any, Dict, Iterator, List, Optional, Tuple

import sqlalchemy as sa

from bgmi.config import cfg
from bgmi.lib.fetch import DATA_SOURCE_MAP
from bgmi.lib.table import Followed, Scripts, Session
from bgmi.utils import print_error, print_info, print_warning
from bgmi.website.model import Episode, WebsiteBangumi


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
                    update_day=model.update_time,
                    id=model.bangumi_name,
                    cover=model.cover,
                )
            )
        return m

    def get_models_dict(self) -> List[dict]:
        return [dict(script.Model()) for script in self.scripts if script.bangumi_name is not None]

    def run(self) -> Iterator[Tuple[Scripts, List[Episode]]]:
        for script in self.scripts:
            print_info(f"fetching {script.bangumi_name} ...")

            try:
                download_item: List[Episode] = [
                    Episode(
                        name=script.bangumi_name,
                        title=f"[{script.bangumi_name}][{k}]",
                        episode=k,
                        download=v,
                    )
                    for k, v in script.get_download_url().items()
                ]
            except Exception as e:
                print_error(f"Failed to fetch script items\nerror: {e}", stop=False)
                continue

            script_obj = script.Model().obj

            if not download_item:
                print_info(f"Got nothing, quit script {script}.")
                continue

            yield script_obj, download_item

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
                with Session.begin() as session:
                    s: Scripts = session.scalar(sa.select(Scripts).where(Scripts.bangumi_name == self.bangumi_name))
                    if not s:
                        s = Scripts(
                            bangumi_name=self.bangumi_name,
                            status=Followed.STATUS_FOLLOWED,
                            updated_time=0,
                        )
                        session.add(s)

                self.obj = s

        def __iter__(self) -> Iterator[Tuple[str, Any]]:
            # patch for cal
            yield "bangumi_name", self.bangumi_name
            yield "cover", self.cover
            yield "update_day", self.update_time
            yield "name", self.bangumi_name
            yield "status", self.obj.status
            yield "updated_time", self.obj.updated_time
            yield "subtitle_group", []
            yield "episode", max(self.obj.episodes) if self.obj.episodes else 0

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
            except KeyError as e:
                raise ValueError(
                    "Script data source is invalid, usable sources: {}".format(", ".join(DATA_SOURCE_MAP.keys()))
                ) from e
            ret = {}
            data = source.fetch_episode_of_bangumi(**self._data)
            for i in data:
                if int(i.episode) not in data:
                    ret[int(i.episode)] = i.download
            return ret

        return {}


if __name__ == "__main__":
    runner = ScriptRunner()
    runner.run()
