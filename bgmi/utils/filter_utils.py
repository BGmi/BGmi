from typing import List

from bgmi.config import config_obj
from bgmi.models import Episode
from bgmi.models.followed import Followed
from bgmi.utils.followed_filter import apply_regex


def apply_keywords_filter_on_list_of_episode(
    followed: Followed,
    episode_list: List[Episode],
) -> List[Episode]:
    episode_list = apply_include(followed, episode_list)
    episode_list = apply_exclude(followed, episode_list)
    episode_list = _apply_regex(followed, episode_list)
    return episode_list


def apply_include(followed: Followed, episode_list: List[Episode]) -> List[Episode]:
    if followed.include:

        def f1(s: Episode):
            return all(map(lambda t: t in s.title, followed.include))

        episode_list = list(filter(f1, episode_list))
    return episode_list


def apply_exclude(followed: Followed, episode_list: List[Episode]) -> List[Episode]:
    if followed.exclude:
        exclude = followed.exclude
    else:
        exclude = []
    if config_obj.ENABLE_GLOBAL_FILTER:
        exclude += config_obj.GLOBAL_FILTER
    exclude.append('合集')

    def f2(s: Episode):
        return not any(map(lambda t: t in s.title, exclude))

    episode_list = list(filter(f2, episode_list))
    return episode_list


def _apply_regex(followed: Followed, episode_list: List[Episode]) -> List[Episode]:
    if followed.regex:
        return apply_regex(followed.regex, episode_list)
    return episode_list
