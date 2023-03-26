from unittest import mock

import pytest

from bgmi.lib.models import Bangumi, Filter, Followed
from bgmi.main import main
from bgmi.website.bangumi_moe import BangumiMoe


def test_gen_nginx_conf():
    main("gen nginx.conf --server-name _".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_cal_force_update():
    class MockWebsite(BangumiMoe):
        def fetch_bangumi_calendar(self):
            bangumi = BangumiMoe().fetch_bangumi_calendar()
            bangumi[0].update_time = "Unknown"
            return bangumi

    with mock.patch("bgmi.lib.controllers.website", MockWebsite()):
        main("cal -f".split())
        assert [
            x.name for x in Bangumi.select().where(Bangumi.update_time == "Unknown")
        ], "at least 1 bangumi's update_time is 'Unknown'"


def test_cal_config():
    main(["config"])


def test_add(bangumi_names):
    main(["add", *bangumi_names])


@pytest.mark.usefixtures("_clean_bgmi")
def test_update(bangumi_names):
    main(["add", *bangumi_names])
    main(["update"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_single(bangumi_names):
    name = bangumi_names[0]
    main(f"add {name}".split())
    main(["update", name])


@pytest.mark.usefixtures("_clean_bgmi")
def test_search(bangumi_names):
    main(["search", "海贼王", "--regex-filter", ".*MP4.*720P.*"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_search_tag(bangumi_names, bangumi_subtitles):
    name = bangumi_names[0]
    subtitle = bangumi_subtitles[0]
    main(["search", "--tag", "--subtitle", subtitle, name, "--regex-filter", ".*720P.*"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_delete(bangumi_names):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(f"delete --name {name}".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_delete_batch(bangumi_names):
    main(["add", *bangumi_names, "--episode", "0"])
    main("delete  --clear-all --batch".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_filter(bangumi_names):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(["filter", name, "--subtitle", "", "--exclude", "MKV", "--regex", "720p|720P"])
    f = Filter.get(bangumi_name=name, exclude="MKV", regex="720p|720P")
    assert not f.include
    assert not f.subtitle


@pytest.mark.usefixtures("_clean_bgmi")
def test_fetch(bangumi_names):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(f"fetch {name}".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_mark(bangumi_names):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(f"mark {name} 1".split())
    assert Followed.get(bangumi_name=name).episode == 1
