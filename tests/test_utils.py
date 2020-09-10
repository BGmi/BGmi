from bgmi.utils import episode_filter_regex, parse_episode
from bgmi.website.model import Episode


def test_print_config():
    title = "[YMDR][哥布林殺手][Goblin Slayer][2018][01][1080p][AVC][JAP][BIG5][MP4-AAC][繁中]"
    episode = parse_episode(title)
    assert episode == 1, episode


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
