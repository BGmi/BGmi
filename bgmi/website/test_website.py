import pytest

from bgmi.website.bangumi_moe import BangumiMoe
from bgmi.website.mikan import Mikanani
from bgmi.website.share_dmhy import DmhySource

bangumi_name_1 = '名偵探柯南'
bangumi_name_2 = '海賊王'

bangumi_1 = {
    'name': bangumi_name_1,
    'id': {
        Mikanani: '227',
        BangumiMoe: '548fe27ef892774b140ac6e8',
        DmhySource: '%E6%9F%AF%E5%8D%97',
    },
}
bangumi_2 = {
    'name': bangumi_name_2,
    'id': {
        Mikanani: '228',
        BangumiMoe: '548ef7225af0fb402813b57b',
        DmhySource: '%E6%B5%B7%E8%B3%8A%E7%8E%8B',
    },
}
test_websites = [
    Mikanani,
    BangumiMoe,
    DmhySource,
]


@pytest.mark.parametrize('website', test_websites)
def test_search(website):
    w = website()
    r = w.search_by_keyword(bangumi_name_1, count=3)
    for b in r:
        assert 'name' in b
        assert 'download' in b
        assert 'title' in b
        assert 'episode' in b


@pytest.mark.parametrize('website', test_websites)
def test_info(website):
    w = website()
    bs, gs = w.fetch_bangumi_calendar_and_subtitle_group()
    b = {}
    for bangumi in bs:
        assert 'status' in bangumi
        assert 'subtitle_group' in bangumi
        assert 'name' in bangumi
        assert 'keyword' in bangumi
        assert 'update_time' in bangumi
        assert 'cover' in bangumi
        if bangumi['keyword'] == bangumi_1['id'][website]:
            b = bangumi

    for subtitle_group in gs:
        assert 'id' in subtitle_group
        assert 'name' in subtitle_group

    assert b

    es = w.fetch_episode_of_bangumi(b['keyword'], 3)
    for episode in es:
        assert 'download' in episode
        assert 'subtitle_group' in episode
        assert 'title' in episode
        assert 'episode' in episode
        assert 'time' in episode
