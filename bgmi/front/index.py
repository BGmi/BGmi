import os
from pprint import pformat
from typing import Dict, List

from bgmi.config import FRONT_STATIC_PATH, SAVE_PATH
from bgmi.front.base import COVER_URL, BaseHandler
from bgmi.lib.models import STATUS_DELETED, STATUS_END, STATUS_UPDATING, Followed
from bgmi.utils import logger, normalize_path


def get_player(bangumi_name: str) -> Dict[int, Dict[str, str]]:
    episode_list = {}
    # new path
    if os.path.exists(os.path.join(SAVE_PATH, normalize_path(bangumi_name))):
        bangumi_name = normalize_path(bangumi_name)
    bangumi_path = os.path.join(SAVE_PATH, bangumi_name)
    path_walk = os.walk(bangumi_path)

    logger.debug("os.walk(bangumi_path) => {}".format(pformat(path_walk)))
    for root, _, files in path_walk:
        _ = root.replace(bangumi_path, "").split(os.path.sep)
        base_path = root.replace(SAVE_PATH, "")
        if len(_) >= 2:
            episode_path = root.replace(os.path.join(SAVE_PATH, bangumi_name), "")
            if episode_path.split(os.path.sep)[1].isdigit():
                episode = int(episode_path.split(os.path.sep)[1])
            else:
                continue
        else:
            episode = -1

        for bangumi in files:
            if any(bangumi.lower().endswith(x) for x in [".mp4", ".mkv", ".webm"]):
                video_file_path = os.path.join(base_path, bangumi)
                video_file_path = os.path.join(
                    os.path.dirname(video_file_path), os.path.basename(video_file_path)
                )
                video_file_path = video_file_path.replace(os.path.sep, "/")
                episode_list[episode] = {"path": video_file_path}
                break

    return episode_list


class IndexHandler(BaseHandler):
    def get(self, path: str) -> None:
        if not os.path.exists(FRONT_STATIC_PATH):
            msg = """<h1>Thanks for your using BGmi</h1>
            <p>It seems you have not install BGmi Frontend,
             please run <code>bgmi install</code> to install.</p>
            """
        else:
            msg = """<h1>Thanks for your using BGmi</h1>
            <p>If use want to use Tornado to serve static files, please run
            <code>bgmi config TORNADO_SERVE_STATIC_FILES 1</code>,
             and do not forget install bgmi-frontend by
            running <code>bgmi install</code></p>"""

        self.write(msg)
        self.finish()


class BangumiListHandler(BaseHandler):
    def get(self, type_: str = "") -> None:
        data: List[dict] = Followed.get_all_followed(
            STATUS_DELETED, STATUS_UPDATING if not type_ == "old" else STATUS_END
        )

        def sorter(_: Dict[str, int]) -> int:
            return _["updated_time"] if _["updated_time"] else 1

        if type_ == "index":
            data.extend(self.patch_list)
            data.sort(key=sorter)

        for bangumi in data:
            bangumi["cover"] = "{}/{}".format(
                COVER_URL, normalize_path(bangumi["cover"])
            )

        data.reverse()

        for item in data:
            item["player"] = get_player(item["bangumi_name"])

        self.write(self.jsonify(data))
        self.finish()
