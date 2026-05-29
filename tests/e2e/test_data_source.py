import pytest

from bgmi.lib.fetch import DATA_SOURCE_MAP
from bgmi.website import mikan
from bgmi.website.base import BaseWebsite
from bgmi.website.model import Episode, SubtitleGroup, WebsiteBangumi


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_info(source, data_source_bangumi_name):
    w: BaseWebsite = DATA_SOURCE_MAP[source]()
    bangumi_result = w.fetch_bangumi_calendar()
    assert bangumi_result, f"website {source} should return bangumi list"
    for bangumi in bangumi_result:
        assert bangumi.cover.startswith("https://") or bangumi.cover.startswith(
            "http://"
        ), "cover not starts with https:// or http://"
        assert isinstance(bangumi, WebsiteBangumi)
        for s in bangumi.subtitle_group:
            assert isinstance(s, SubtitleGroup)
    b = bangumi_result[0]

    w.fetch_episode_of_bangumi(b.id, max_page=3)
    w.fetch_single_bangumi(b.id)


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_search(source, data_source_bangumi_name):
    w = DATA_SOURCE_MAP[source]()
    names = data_source_bangumi_name[source]
    for name in names:
        search_result = w.search_by_keyword(name, count=1)
        if search_result:
            for episode in search_result:
                assert isinstance(episode, Episode)
            return
    pytest.fail(f"search_by_keyword returned empty for all {len(names)} names on {source}: {names}")


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_search_tag(source, data_source_subtitle_name):
    w = DATA_SOURCE_MAP[source]()

    assert source in data_source_subtitle_name, f"No subtitle data found for {source}"

    pairs = data_source_subtitle_name[source]
    for bangumi_name, subtitle_name in pairs:
        try:
            search_result = w.search_by_tag(bangumi_name, subtitle_name, count=1)
        except Exception:
            continue
        if search_result:
            for episode in search_result:
                assert isinstance(episode, Episode)
            return
    pytest.fail(f"search_by_tag returned empty for all {len(pairs)} pairs on {source}: {pairs}")


def test_mikan_fetch_all_episode():
    """
    大欺诈师 极影字幕社

    https://mikanani.me/Home/Bangumi/2242
    """
    w = mikan.Mikanani()
    results = w.fetch_episode_of_bangumi("2242", subtitle_list=["34"])
    assert len(results) > 15, "should fetch more episode in expand button"
