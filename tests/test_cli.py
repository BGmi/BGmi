from unittest import mock

from bgmi.lib.models import Bangumi, Filter, Followed
from bgmi.main import main
from bgmi.website.bangumi_moe import BangumiMoe


def test_gen_nginx_conf():
    main("gen nginx.conf --server-name _".split())


def test_cal_force_update(clean_bgmi):
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
    main("config".split())
    main("config ADMIN_TOKEN 233".split())
    main("config DOWNLOAD_DELEGATE xunlei".split())
    main("config BANGUMI_MOE_URL https://bangumi.moe".split())


def test_add(bangumi_names, clean_bgmi):
    main("add {} {} {}".format(*bangumi_names).split())


def test_update(bangumi_names, clean_bgmi):
    main("add {} {} {}".format(*bangumi_names).split())
    main(["update"])


def test_update_single(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main(f"add {name}".split())
    main(["update", name])


def test_search(bangumi_names, clean_bgmi):
    main(["search", "海贼王", "--regex-filter", ".*MP4.*720P.*"])


def test_delete(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(f"delete --name {name}".split())


def test_delete_batch(bangumi_names, clean_bgmi):
    main("add {} {} {} --episode 0".format(*bangumi_names).split())
    main("delete  --clear-all --batch".split())


def test_filter(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(["filter", name, "--subtitle", "", "--exclude", "MKV", "--regex", "720p|720P"])
    f = Filter.get(bangumi_name=name, exclude="MKV", regex="720p|720P")
    assert not f.include
    assert not f.subtitle


def test_fetch(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(f"fetch {name}".split())


def test_mark(bangumi_names, clean_bgmi):
    name = bangumi_names[0]
    main(f"add {name} --episode 0".split())
    main(f"mark {name} 1".split())
    assert Followed.get(bangumi_name=name).episode == 1
