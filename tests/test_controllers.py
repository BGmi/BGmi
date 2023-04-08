from unittest import mock

import pytest

from bgmi.lib import controllers as ctl
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.controllers import cal, recreate_source_relatively_table
from bgmi.lib.table import Followed, NotFoundError

bangumi_name_1 = "名侦探柯南"
bangumi_name_2 = "海贼王"


def test_add(ensure_data):
    r = ctl.add(bangumi_name_2, 0)
    assert r["status"] == "success", r["message"]

    r = ctl.add(bangumi_name_2, 0)
    assert r["status"] == "warning", r["message"]


def test_mark(ensure_data):
    ctl.mark(bangumi_name_1, 0)

    assert Followed.get(Followed.bangumi_name == bangumi_name_1).episode == 0

    r = ctl.mark(bangumi_name_2, 0)
    assert r["status"] == "error", r["message"]


def test_filter(ensure_data):
    ctl.filter_(
        bangumi_name_1,
        subtitle="sg1",
        include="include",
        exclude="exclude",
        regex="regex",
    )

    f = Followed.get(Followed.bangumi_name == bangumi_name_1)

    assert f.subtitle == ["id1"]
    assert f.include == ["include"]
    assert f.exclude == ["exclude"]
    assert f.regex == "regex"


def test_delete(ensure_data):
    r = ctl.delete(bangumi_name_1)
    assert r["status"] == "warning", r["message"]
    r = ctl.delete(bangumi_name_1)
    assert r["status"] == "warning", r["message"]
    r = ctl.delete(bangumi_name_1)
    assert r["status"] == "warning", r["message"]

    r = ctl.delete(bangumi_name_2)
    assert r["status"] == "error", r["message"]

    r = ctl.delete(clear_all=True, batch=True)
    assert r["status"] == "warning", r["message"]

    with pytest.raises(NotFoundError):
        Followed.get(Followed.bangumi_name == bangumi_name_1)

    with pytest.raises(NotFoundError):
        assert Followed.get(Followed.bangumi_name == bangumi_name_2)


def test_search():
    with mock.patch("bgmi.lib.fetch.website.search_by_keyword") as m:
        m.return_value = []
        ctl.search(bangumi_name_1, dupe=False)


def test_cal():
    recreate_source_relatively_table()

    r = cal(force_update=True)
    assert isinstance(r, dict)
    for day in r.keys():
        assert day.lower() in (x.lower() for x in BANGUMI_UPDATE_TIME)
        assert isinstance(r[day], list)
        for bangumi in r[day]:
            assert "status" in bangumi
            assert "subtitle_group" in bangumi
            assert "name" in bangumi
            assert "update_time" in bangumi
            assert "cover" in bangumi
            assert "episode" in bangumi
