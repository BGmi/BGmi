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

    w.fetch_episode_of_bangumi(b.keyword, max_page=3)
    w.fetch_single_bangumi(b.keyword)


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_search(source, data_source_bangumi_name):
    w = DATA_SOURCE_MAP[source]()
    search_result = w.search_by_keyword(data_source_bangumi_name[source][0], count=1)
    assert search_result
    for episode in search_result:
        assert isinstance(episode, Episode)


def test_mikan_fetch_all_episode():
    """
    大欺诈师 极影字幕社

    https://mikanani.me/Home/Bangumi/2242
    """
    w = mikan.Mikanani()
    results = w.fetch_episode_of_bangumi("2242", subtitle_list=["34"])
    assert len(results) > 15, "should fetch more episode in expand button"
