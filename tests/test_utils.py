from typing import List, Tuple

import pytest

from bgmi.utils import episode_filter_regex, parse_episode
from bgmi.website.model import Episode

_episode_cases: List[Tuple[str, int]] = [
    (
        "[YMDR][哥布林殺手][Goblin Slayer][2018][01][1080p][AVC][JAP][BIG5][MP4-AAC][繁中]",
        1,
    ),
    ("【安達與島村】【第二話】【1080P】【繁體中文】【AVC】", 2),
    ("のんのんびより のんすとっぷ 第02话 BIG5 720p MP4", 2),
    ("OVA 噬血狂袭 Strike the Blood IV [E01][720P][GB][BDrip]", 1),
    ("Kumo Desu ga, Nanika - 01 v2 [1080p][繁体]", 1),
    ("Re Zero Isekai Seikatsu S02 - 17 [Baha][1080p][AVC AAC]", 17),
    # range as 0
    ("[从零开始的异世界生活 第二季_Re Zero S2][34-35][繁体][720P][MP4]", 0),
    ("Strike The Blood IV][OVA][05-06][1080P][GB][MP4]", 0),
    ("[Legend of the Galactic Heroes 银河英雄传说][全110话+外传+剧场版][MKV][外挂繁中]", 0),
    ("不知道什么片 全二十话", 0),
    ("不知道什么片 全20话", 0),
    (
        ("[Lilith-Raws] 如果究极进化的完全沉浸 RPG 比现实还更像垃圾游戏的话 / Full Dive - 02 " "[Baha][WEB-DL][1080p][AVC AAC][CHT][MP4]"),
        2,
    ),
    (
        "[Lilith-Raws] 86 - Eighty Six - 01 [Baha][WEB-DL][1080p][AVC AAC][CHT][MP4]",
        1,
    ),
]


@pytest.mark.parametrize(("title", "episode"), _episode_cases)
def test_episode_parse(title, episode):
    assert (
        parse_episode(title) == episode
    ), f"\ntitle: {title!r}\nepisode: {episode}\nparsed episode: {parse_episode(title)}"


def test_remove_dupe():
    e = Episode.remove_duplicated_bangumi(
        [
            Episode(name="1", title="1", download="1", episode=1),
            Episode(name="1", title="1", download="1", episode=1),
            Episode(name="2", title="2", download="2", episode=2),
            Episode(name="2", title="2", download="2", episode=2),
            Episode(name="3", title="3", download="3", episode=3),
            Episode(name="5", title="5", download="5", episode=5),
        ]
    )
    assert len(e) == 4, e
    assert {x.episode for x in e} == {1, 2, 3, 5}


def test_episode_regex():
    e = episode_filter_regex(
        [
            Episode(name="1", title="720", download="1", episode=1),
            Episode(name="2", title="1080", download="1", episode=1),
            Episode(name="2", title="23", download="2", episode=2),
            Episode(name="1", title="17202", download="2", episode=2),
            Episode(name="3", title="..71..", download="3", episode=3),
            Episode(name="5", title="no", download="5", episode=5),
        ],
        ".*720.*",
    )
    assert len(e) == 2, e
    assert {x.name for x in e} == {"1"}


def test_episode_exclude_word():
    assert Episode(title="a b c", download="").contains_any_words(["a"])
    assert Episode(title="A B c", download="").contains_any_words(["a", "b"])
    assert not Episode(title="a b c", download="").contains_any_words(["d", "ab"])
