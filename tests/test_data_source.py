import pytest

from bgmi.lib.fetch import DATA_SOURCE_MAP
from bgmi.website.base import BaseWebsite
from bgmi.website.model import SubtitleGroup, WebsiteBangumi


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_info(source, data_source_bangumi_name):
    w = DATA_SOURCE_MAP[source]()  # type: BaseWebsite
    bangumi_result = w.fetch_bangumi_calendar()
    assert bangumi_result, "website {} should return bangumi list".format(source)
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
    assert w.search_by_keyword(data_source_bangumi_name[source][0])
