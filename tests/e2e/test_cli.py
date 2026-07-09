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
    main_for_test(["config", "--help"])


def test_install_refreshes_crontab():
    with (
        mock.patch("bgmi.main.create_dir"),
        mock.patch("bgmi.main.init_db"),
        mock.patch("bgmi.main.install_crontab") as install_crontab,
        mock.patch("bgmi.main.write_default_config"),
        mock.patch("bgmi.main.update_database"),
    ):
        main_for_test(["install", "--no-web"])

    install_crontab.assert_called_once()


@pytest.mark.usefixtures("_clean_bgmi")
def test_list_with_empty_seen_episodes():
    Bangumi(id="empty-seen", name="Empty Seen", update_day="Mon").save()
    Followed(bangumi_name="Empty Seen", episodes=set()).save()

    main_for_test(["list"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_cal_with_empty_seen_episodes():
    Bangumi(id="empty-seen", name="Empty Seen", update_day="Mon").save()
    Followed(bangumi_name="Empty Seen", episodes=set()).save()

    main_for_test(["cal"])


@pytest.mark.usefixtures("_ensure_data")
def test_add():
    main_for_test(["add", bangumi_name_2, "--episode", "1"])
    assert Followed.get(Followed.bangumi_name == bangumi_name_2).status == Followed.STATUS_FOLLOWED
    assert Followed.get(Followed.bangumi_name == bangumi_name_2).episode == 1


@pytest.mark.usefixtures("_ensure_data")
def test_seen_forget():
    f = Followed.get(Followed.bangumi_name == bangumi_name_1)
    assert 2 in f.episodes
    main_for_test(["seen", "forget", bangumi_name_1, "2"])
    f = Followed.get(Followed.bangumi_name == bangumi_name_1)
    assert 2 not in f.episodes


@pytest.mark.usefixtures("_ensure_data")
def test_seen_mark():
    f = Followed.get(Followed.bangumi_name == bangumi_name_1)
    assert 3 not in f.episodes
    main_for_test(["seen", "mark", bangumi_name_1, "3"])
    f = Followed.get(Followed.bangumi_name == bangumi_name_1)
    assert 3 in f.episodes


@pytest.mark.usefixtures("_clean_bgmi")
def test_update(bangumi_names):
    main_for_test(["add", *bangumi_names])
    main_for_test(["update"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_script():
    main_for_test(["update"])
    script_obj = ScriptRunner().get_model("TEST_BANGUMI")
    assert script_obj.episodes == {2, 3}, "TEST_BANGUMI from script_example.py episode should be {2, 3} after update"


@pytest.mark.usefixtures("_clean_bgmi")
def test_update_single(bangumi_names):
    name = bangumi_names[0]
    main_for_test(["add", name])
    main_for_test(["update", name])


@pytest.mark.usefixtures("_clean_bgmi")
def test_search(bangumi_names):
    main_for_test(["search", bangumi_names[0], "--regex-filter", ".*"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_search_tag(bangumi_names, bangumi_subtitles):
    name = bangumi_names[0]
    subtitle = bangumi_subtitles[0]
    main_for_test(["search", "--tag", "--subtitle", subtitle, name, "--regex-filter", ".*720P.*"])


@pytest.mark.usefixtures("_clean_bgmi")
def test_delete(bangumi_names):
    name = bangumi_names[0]
    main_for_test(["add", name, "--episode", "0"])
    main_for_test(["delete", name])


@pytest.mark.usefixtures("_clean_bgmi")
def test_delete_batch(bangumi_names):
    main_for_test(["add", *bangumi_names, "--episode", "0"])
    main_for_test("delete  --clear-all --yes".split())


@pytest.mark.usefixtures("_clean_bgmi")
def test_filter(bangumi_names):
    name = bangumi_names[0]
    main_for_test(["add", name, "--episode", "0"])
    main_for_test(["filter", name, "--subtitle", "", "--exclude", "MKV", "--regex", "720p|720P"])
    f = Followed.get(Followed.bangumi_name == name)
    assert not f.include
    assert not f.subtitle


@pytest.mark.usefixtures("_clean_bgmi")
def test_fetch(bangumi_names):
    name = bangumi_names[0]
    main_for_test(["add", name, "--episode", "0"])
    main_for_test(["fetch", name])
