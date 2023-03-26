import os
from pprint import pformat
from typing import Dict, List

from bgmi.config import cfg
from bgmi.front.base import COVER_URL, BaseHandler
from bgmi.lib.models import STATUS_DELETED, STATUS_END, STATUS_UPDATING, Followed
from bgmi.utils import logger, normalize_path


def get_player(bangumi_name: str) -> Dict[int, Dict[str, str]]:
    episode_list = {}
    # new path
    if cfg.save_path.joinpath(normalize_path(bangumi_name)).exists():
        bangumi_name = normalize_path(bangumi_name)
    bangumi_path = cfg.save_path.joinpath(bangumi_name)
    path_walk = os.walk(bangumi_path)

    logger.debug("os.walk(bangumi_path) => %s", pformat(path_walk))
    for root, _, files in path_walk:
        _ = root.replace(str(bangumi_path), "").split(os.path.sep)
        base_path = root.replace(str(cfg.save_path), "")
        if len(_) >= 2:
            episode_path = root.replace(os.path.join(cfg.save_path, bangumi_name), "")
            if episode_path.split(os.path.sep)[1].isdigit():
                episode = int(episode_path.split(os.path.sep)[1])
            else:
                continue
        else:
            episode = -1

        sorted_files = sorted(
            files,
            key=lambda f: os.path.getsize(os.path.join(root, f)),  # noqa: B023
            reverse=True,
        )

        for bangumi in sorted_files:
            if any(bangumi.lower().endswith(x) for x in [".mp4", ".mkv", ".webm"]):
                video_file_path = os.path.join(base_path, bangumi)
                video_file_path = os.path.join(os.path.dirname(video_file_path), os.path.basename(video_file_path))
                video_file_path = video_file_path.replace(os.path.sep, "/")
                episode_list[episode] = {"path": video_file_path}
                break

    return episode_list


class IndexHandler(BaseHandler):
    def get(self, path: str) -> None:
        if not os.path.exists(cfg.front_static_path):
            msg = """<h1>Thanks for your using BGmi</h1>
            <p>It seems you have not install BGmi Frontend,
             please run <code>bgmi install</code> to install.</p>
            """
        else:
            msg = """<h1>Thanks for your using BGmi</h1>
            <p>If use want to use Tornado to serve static files, please enable
            <code>[bgmi_http]</code>,
            <code>serve_static_files = false</code>,
            and do not forget install bgmi-frontend by
            running <code>bgmi install</code></p>"""

        self.write(msg)
        self.finish()


class BangumiListHandler(BaseHandler):
    def get(self, type_: str = "") -> None:
        data: List[dict] = Followed.get_all_followed(STATUS_DELETED, STATUS_END if type_ == "old" else STATUS_UPDATING)

        def sorter(_: Dict[str, int]) -> int:
            return _["updated_time"] if _["updated_time"] else 1

        if type_ == "index":
            data.extend(self.patch_list)
            data.sort(key=sorter)

        for bangumi in data:
            bangumi["cover"] = "{}/{}".format(COVER_URL, normalize_path(bangumi["cover"]))

        data.reverse()

        for item in data:
            item["player"] = get_player(item["bangumi_name"])

        self.write(self.jsonify(data))
        self.finish()
