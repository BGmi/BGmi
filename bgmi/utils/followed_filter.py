import os
import re
from typing import List

from bgmi.lib.models import Episode


def apply_regex(regex, episode_list: List[Episode]) -> List[Episode]:
    try:
        match = re.compile(regex)
        episode_list = [s for s in episode_list if match.findall(s.title)]
    except re.error as exc:
        if os.getenv('DEBUG'):  # pragma: no cover
            import traceback

            traceback.print_exc()
            raise exc
        return episode_list
    return episode_list
