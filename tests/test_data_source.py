import pytest

from bgmi.lib.fetch import DATA_SOURCE_MAP


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_info(source, data_source_bangumi_name):
    w = DATA_SOURCE_MAP[source]()
    bs, gs = w.fetch_bangumi_calendar_and_subtitle_group()
    assert bs, "website {} should return bangumi list".format(source)
    assert gs, "website {} should return subtitle_group list".format(source)
    for bangumi in bs:
        assert "status" in bangumi
        assert "subtitle_group" in bangumi
        assert "name" in bangumi
        assert "keyword" in bangumi
        assert "update_time" in bangumi
        assert "cover" in bangumi

    for subtitle_group in gs:
        assert "id" in subtitle_group
        assert "name" in subtitle_group

    b = bs[0]

    es = w.fetch_episode_of_bangumi(b["keyword"])
    for episode in es:
        assert "download" in episode
        assert "subtitle_group" in episode
        assert "title" in episode
        assert "episode" in episode
        assert "time" in episode


@pytest.mark.parametrize("source", DATA_SOURCE_MAP.keys())
def test_search(source, data_source_bangumi_name):
    w = DATA_SOURCE_MAP[source]()
    r = w.search_by_keyword(data_source_bangumi_name[source][0])
    for b in r:
        assert "name" in b
        assert "download" in b
        assert "title" in b
        assert "episode" in b
