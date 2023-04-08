from unittest import mock

import pytest

from bgmi.lib.table import Bangumi, Followed
from bgmi.main import main_for_test
from bgmi.script import ScriptRunner
from bgmi.website.bangumi_moe import BangumiMoe
from tests.conftest import bangumi_name_1, bangumi_name_2


def test_gen_nginx_conf():
    main_for_test("gen nginx.conf --server-name _".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_cal_force_update():
    class MockWebsite(BangumiMoe):
        def fetch_bangumi_calendar(self):
            bangumi = BangumiMoe().fetch_bangumi_calendar()
            bangumi[0].update_day = "Unknown"
            return bangumi

    with mock.patch("bgmi.lib.controllers.website", MockWebsite()):
        main_for_test("cal -f".split())
        assert [
            x.name for x in Bangumi.all(Bangumi.update_day == "Unknown")
        ], "at least 1 bangumi's update_time is 'Unknown'"


def test_cal_config():
    main_for_test(["config"])


@pytest.mark.usefixtures("ensure_data")
def test_add():
    main_for_test(["add", bangumi_name_2, "--episode", "1"])
    assert Followed.get(Followed.bangumi_name == bangumi_name_2).status == Followed.STATUS_FOLLOWED
    assert Followed.get(Followed.bangumi_name == bangumi_name_2).episode == 1


@pytest.mark.usefixtures("ensure_data")
def test_mark():
    main_for_test(f"mark {bangumi_name_1} 10".split())
    assert Followed.get(Followed.bangumi_name == bangumi_name_1).episode == 10


@pytest.mark.usefixtures("_clean_bgmi")
def test_update(bangumi_names):
    main_for_test(["add", *bangumi_names])
    main_for_test(["update"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_script():
    main_for_test(["update"])
    script_obj = ScriptRunner().get_model("TEST_BANGUMI")
    assert script_obj.episode == 3, "TEST_BANGUMI from script_example.py episode should be 3 after update"


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_single(bangumi_names):
    name = bangumi_names[0]
    main_for_test(f"add {name}".split())
    main_for_test(["update", name])


@pytest.mark.usefixtures("_clean_bgmi")
def test_search(bangumi_names):
    main_for_test(["search", "海贼王", "--regex-filter", ".*MP4.*720P.*"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_search_tag(bangumi_names, bangumi_subtitles):
    name = bangumi_names[0]
    subtitle = bangumi_subtitles[0]
    main_for_test(["search", "--tag", "--subtitle", subtitle, name, "--regex-filter", ".*720P.*"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_delete(bangumi_names):
    name = bangumi_names[0]
    main_for_test(f"add {name} --episode 0".split())
    main_for_test(f"delete {name}".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_delete_batch(bangumi_names):
    main_for_test(["add", *bangumi_names, "--episode", "0"])
    main_for_test("delete  --clear-all --yes".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_filter(bangumi_names):
    name = bangumi_names[0]
    main_for_test(f"add {name} --episode 0".split())
    main_for_test(["filter", name, "--subtitle", "", "--exclude", "MKV", "--regex", "720p|720P"])
    f = Followed.get(Followed.bangumi_name == name)
    assert not f.include
    assert not f.subtitle


@pytest.mark.usefixtures("_clean_bgmi")
def test_fetch(bangumi_names):
    name = bangumi_names[0]
    main_for_test(f"add {name} --episode 0".split())
    main_for_test(f"fetch {name}".split())
