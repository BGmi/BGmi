import os
from pathlib import Path
from typing import Dict, Optional

from bgmi.config import cfg
from bgmi.utils import bangumi_save_path


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
