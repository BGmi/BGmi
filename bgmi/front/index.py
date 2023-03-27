import os
from pathlib import Path
from typing import Dict, List, Optional

from bgmi.config import cfg
from bgmi.front.base import COVER_URL, BaseHandler
from bgmi.lib.models import STATUS_DELETED, STATUS_END, STATUS_UPDATING, Followed
from bgmi.utils import bangumi_save_path, normalize_path


def get_player(bangumi_name: str) -> Dict[int, Dict[str, str]]:
    bangumi_path = bangumi_save_path(bangumi_name)

    if not bangumi_path.exists():
        return {}

    episode_list = {}

    episodes = [episode.name for episode in bangumi_path.iterdir() if episode.name.isdigit()]

    for episode in episodes:
        e = find_largest_video_file(bangumi_path.joinpath(episode))
        if e:
            episode_list[int(episode)] = {"path": "/" + e}

    return episode_list


def find_largest_video_file(top_dir: Path) -> Optional[str]:
    video_files = []
    for root, _, files in os.walk(top_dir):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in [".mp4", ".mkv", ".webm"]:
                p = Path(root).joinpath(file)
                video_files.append((p.stat().st_size, p))

    if not video_files:
        return None

    video_files.sort(key=lambda x: -x[0])

    return video_files[0][1].relative_to(cfg.save_path).as_posix()


if __name__ == "__main__":
    print(get_player("test-save-path"))


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
            <code>[http]</code>,
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
