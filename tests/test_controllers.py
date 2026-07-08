import datetime
from unittest import mock

import pytest

from bgmi.lib import controllers as ctl
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.controllers import cal
from bgmi.lib.table import Bangumi, Download, Followed, NotFoundError, Session, recreate_source_relatively_table
from bgmi.website.model import WebsiteBangumi

bangumi_name_1 = "名侦探柯南"
bangumi_name_2 = "海贼王"


def _timestamp(year: int, month: int, day: int, hour: int = 12) -> int:
    return int(datetime.datetime(year, month, day, hour).timestamp())


@pytest.mark.usefixtures("_ensure_data")
def test_add():
    r = ctl.add(bangumi_name_2, 0)
    assert r["status"] == "success", r["message"]

    r = ctl.add(bangumi_name_2, 0)
    assert r["status"] == "warning", r["message"]


def test_followed_lifecycle_resets_stale_updated_status():
    recreate_source_relatively_table()
    now = _timestamp(2026, 7, 8)
    yesterday = _timestamp(2026, 7, 7)
    with Session.begin() as tx:
        tx.add(Bangumi(id="updated-yesterday", name="Updated Yesterday", update_day="Tue"))
        tx.add(
            Followed(
                bangumi_name="Updated Yesterday",
                episodes={1},
                status=Followed.STATUS_UPDATED,
                updated_time=yesterday,
            )
        )

    Followed.refresh_lifecycle(now=now)

    assert Followed.get(Followed.bangumi_name == "Updated Yesterday").status == Followed.STATUS_FOLLOWED


def test_followed_lifecycle_resets_updated_status_without_timestamp():
    recreate_source_relatively_table()
    now = _timestamp(2026, 7, 8)
    with Session.begin() as tx:
        tx.add(Bangumi(id="updated-without-time", name="Updated Without Time", update_day="Tue"))
        tx.add(
            Followed(
                bangumi_name="Updated Without Time",
                episodes={1},
                status=Followed.STATUS_UPDATED,
                updated_time=0,
            )
        )

    Followed.refresh_lifecycle(now=now)

    assert Followed.get(Followed.bangumi_name == "Updated Without Time").status == Followed.STATUS_FOLLOWED


def test_followed_lifecycle_keeps_today_updated_status():
    recreate_source_relatively_table()
    now = _timestamp(2026, 7, 8, 18)
    today = _timestamp(2026, 7, 8, 9)
    with Session.begin() as tx:
        tx.add(Bangumi(id="updated-today", name="Updated Today", update_day="Wed"))
        tx.add(
            Followed(
                bangumi_name="Updated Today",
                episodes={1},
                status=Followed.STATUS_UPDATED,
                updated_time=today,
            )
        )

    Followed.refresh_lifecycle(now=now)

    assert Followed.get(Followed.bangumi_name == "Updated Today").status == Followed.STATUS_UPDATED


def test_bangumi_lifecycle_marks_ended_after_two_weeks_without_updates():
    recreate_source_relatively_table()
    now = _timestamp(2026, 7, 20)
    end_after_seconds = 2 * 7 * 24 * 3600
    with Session.begin() as tx:
        tx.add(Bangumi(id="old", name="Old", status=Bangumi.STATUS_UPDATING))
        tx.add(Bangumi(id="recent", name="Recent", status=Bangumi.STATUS_UPDATING))
        tx.add(
            Followed(
                bangumi_name="Old",
                episodes={12},
                status=Followed.STATUS_FOLLOWED,
                updated_time=now - end_after_seconds - 1,
            )
        )
        tx.add(
            Followed(
                bangumi_name="Recent",
                episodes={1},
                status=Followed.STATUS_FOLLOWED,
                updated_time=now - end_after_seconds + 1,
            )
        )

    with mock.patch("bgmi.lib.table.time.time", return_value=now):
        Bangumi.mark_all_end()

    assert Bangumi.get(Bangumi.name == "Old").status == Bangumi.STATUS_END
    assert Bangumi.get(Bangumi.name == "Recent").status == Bangumi.STATUS_UPDATING
    assert Followed.get(Followed.bangumi_name == "Old").status == Followed.STATUS_FOLLOWED


def test_followed_lifecycle_does_not_manage_ended_bangumi_status():
    recreate_source_relatively_table()
    now = _timestamp(2026, 7, 20)
    with Session.begin() as tx:
        tx.add(Bangumi(id="ended", name="Ended", status=Bangumi.STATUS_END))
        tx.add(
            Followed(
                bangumi_name="Ended",
                episodes={12},
                status=Followed.STATUS_FOLLOWED,
                updated_time=now - 2 * 7 * 24 * 3600 - 1,
            )
        )

    Followed.refresh_lifecycle(now=now)

    assert Followed.get(Followed.bangumi_name == "Ended").status == Followed.STATUS_FOLLOWED
    assert Bangumi.get(Bangumi.name == "Ended").status == Bangumi.STATUS_END


def test_add_defaults_to_no_seen_episodes():
    recreate_source_relatively_table()
    name = "Default Episode Zero"
    with Session.begin() as tx:
        tx.add(Bangumi(id="default-episode-zero", name=name, update_day="Mon"))

    with mock.patch("bgmi.lib.controllers.website.get_maximum_episode") as get_maximum_episode:
        r = ctl.add(name)

    assert r["status"] == "success", r["message"]
    get_maximum_episode.assert_not_called()
    assert Followed.get(Followed.bangumi_name == name).episodes == set()


def test_add_can_mark_currently_available_episodes():
    recreate_source_relatively_table()
    name = "Already Aired"
    with Session.begin() as tx:
        tx.add(Bangumi(id="already-aired", name=name, update_day="Mon"))

    with mock.patch("bgmi.lib.controllers.website.get_maximum_episode") as get_maximum_episode:
        get_maximum_episode.return_value = [
            mock.Mock(episode=1),
            mock.Mock(episode=2),
            mock.Mock(episode=3),
        ]
        r = ctl.add(name, episode=None)

    assert r["status"] == "success", r["message"]
    get_maximum_episode.assert_called_once()
    assert Followed.get(Followed.bangumi_name == name).episodes == {1, 2, 3}


def test_add_auto_display_name_from_season_suffix():
    recreate_source_relatively_table()
    name = "相反的你和我 第二季"
    with Session.begin() as tx:
        tx.add(Bangumi(id="opposite-you-and-me-s2", name=name, update_day="Mon"))

    r = ctl.add(name, 0)

    assert r["status"] == "success", r["message"]
    assert "detected season 2" in r["message"]
    assert "path display name normalized to 相反的你和我" in r["message"]
    followed = Followed.get(Followed.bangumi_name == name)
    assert followed.season == 2
    assert followed.display_name == "相反的你和我"


def test_add_explicit_display_name_skips_auto_display_name():
    recreate_source_relatively_table()
    name = "相反的你和我 第二季"
    with Session.begin() as tx:
        tx.add(Bangumi(id="opposite-you-and-me-s2", name=name, update_day="Mon"))

    r = ctl.add(name, 0, display_name="You and I Are Polar Opposites")

    assert r["status"] == "success", r["message"]
    assert "path display name normalized" not in r["message"]
    followed = Followed.get(Followed.bangumi_name == name)
    assert followed.season == 2
    assert followed.display_name == "You and I Are Polar Opposites"


def test_add_explicit_season_reports_detected_and_used_season():
    recreate_source_relatively_table()
    name = "爱书的下克上 第4季"
    with Session.begin() as tx:
        tx.add(Bangumi(id="bookworm-s4", name=name, update_day="Mon"))

    r = ctl.add(name, 0, season=1)

    assert r["status"] == "success", r["message"]
    assert "detected season 4, using season 1" in r["message"]
    followed = Followed.get(Followed.bangumi_name == name)
    assert followed.season == 1
    assert followed.display_name == "爱书的下克上"


@pytest.mark.usefixtures("_ensure_data")
def test_filter():
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


@pytest.mark.usefixtures("_ensure_data")
def test_delete():
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


@pytest.mark.usefixtures("_ensure_data")
def test_seen():
    result = ctl.seen(bangumi_name_1)

    assert result["status"] == "success"
    assert result["bangumi"] == bangumi_name_1
    assert result["total_episode"] == 2
    assert result["seen"] == [1, 2]


@pytest.mark.usefixtures("_ensure_data")
def test_seen_forget_resets_download_record():
    with Session.begin() as tx:
        tx.add(
            Download(
                bangumi_name=bangumi_name_1,
                episode=2,
                title="episode 2",
                download="magnet:?xt=urn:btih:2",
                status=Download.STATUS_DOWNLOADED,
                task_id="task-2",
            )
        )

    result = ctl.seen_forget(bangumi_name_1, 2)

    assert result["status"] == "success"
    assert result["episode"] == 2
    assert result["seen"] == [1]
    assert result["total_episode"] == 2
    assert 2 not in Followed.get(Followed.bangumi_name == bangumi_name_1).episodes
    download = Download.get(Download.bangumi_name == bangumi_name_1, Download.episode == 2)
    assert download.status == Download.STATUS_NOT_DOWNLOAD
    assert download.task_id is None


@pytest.mark.usefixtures("_ensure_data")
def test_seen_mark_updates_download_record():
    with Session.begin() as tx:
        tx.add(
            Download(
                bangumi_name=bangumi_name_1,
                episode=3,
                title="episode 3",
                download="magnet:?xt=urn:btih:3",
                status=Download.STATUS_DOWNLOADING,
                task_id="task-3",
            )
        )

    result = ctl.seen_mark(bangumi_name_1, 3)

    assert result["status"] == "success"
    assert result["episode"] == 3
    assert result["seen"] == [1, 2, 3]
    assert result["total_episode"] == 3
    assert 3 in Followed.get(Followed.bangumi_name == bangumi_name_1).episodes
    download = Download.get(Download.bangumi_name == bangumi_name_1, Download.episode == 3)
    assert download.status == Download.STATUS_DOWNLOADED
    assert download.task_id is None


def test_search():
    with mock.patch("bgmi.lib.fetch.website.search_by_keyword") as m:
        m.return_value = []
        ctl.search(bangumi_name_1, dupe=False)


def test_cal():
    recreate_source_relatively_table()

    r = cal(force_update=True)
    assert isinstance(r, dict)
    for day in r:
        assert day.lower() in (x.lower() for x in BANGUMI_UPDATE_TIME)
        assert isinstance(r[day], list)
        for bangumi in r[day]:
            assert "status" in bangumi
            assert "subtitle_group" in bangumi
            assert "name" in bangumi
            assert "update_day" in bangumi
            assert "cover" in bangumi
            assert "episode" in bangumi


def test_cal_download_cover_skips_empty_cover():
    weekly_list = {
        "mon": [
            {
                "name": "No Cover",
                "update_day": "Mon",
                "cover": "",
                "subtitle_group": [],
                "status": 0,
                "episode": 0,
            }
        ]
    }

    with (
        mock.patch(
            "bgmi.lib.controllers.Bangumi.get_updating_bangumi",
            return_value=weekly_list,
        ),
        mock.patch("bgmi.lib.controllers.ScriptRunner") as script_runner,
        mock.patch("bgmi.lib.controllers._refresh_missing_followed_covers") as refresh_missing_followed_covers,
        mock.patch("bgmi.lib.controllers.filetype.is_image") as is_image,
        mock.patch("bgmi.lib.controllers.download_cover") as download_cover,
    ):
        script_runner.return_value.get_models_dict.return_value = []

        r = cal(cover=[])

    assert r["mon"][0]["cover"] == ""
    refresh_missing_followed_covers.assert_called_once_with()
    is_image.assert_not_called()
    download_cover.assert_not_called()


def test_cal_download_cover_refreshes_followed_empty_cover():
    bangumi_name = "No Cover Followed"
    cover_url = "https://example.com/cover.jpg"
    recreate_source_relatively_table()
    with Session.begin() as tx:
        tx.add(Bangumi(id="no-cover", name=bangumi_name, update_day="Mon", cover=""))
        tx.add(Followed(bangumi_name=bangumi_name, episodes=set()))

    with (
        mock.patch(
            "bgmi.lib.controllers.website.fetch_single_bangumi",
            return_value=WebsiteBangumi(id="no-cover", name=bangumi_name, update_day="Mon", cover=cover_url),
        ) as fetch_single_bangumi,
        mock.patch("bgmi.lib.controllers.ScriptRunner") as script_runner,
        mock.patch("bgmi.lib.controllers.download_cover") as download_cover,
    ):
        script_runner.return_value.get_models_dict.return_value = []

        r = cal(cover=[])

    fetch_single_bangumi.assert_called_once()
    download_cover.assert_called_once_with([cover_url])
    assert Bangumi.get(Bangumi.name == bangumi_name).cover == cover_url
    assert r["mon"][0]["cover"] == "https/example.com/cover.jpg"


def test_cal_download_cover_refreshes_invalid_badge_cover():
    bangumi_name = "Badge Cover Followed"
    badge_url = "https://mikanani.me/images/subscribed-badge.svg"
    cover_url = "https://mikanani.me/images/Bangumi/202604/c68609a0.jpg"
    recreate_source_relatively_table()
    with Session.begin() as tx:
        tx.add(Bangumi(id="badge-cover", name=bangumi_name, update_day="Mon", cover=badge_url))
        tx.add(Followed(bangumi_name=bangumi_name, episodes=set()))

    with (
        mock.patch(
            "bgmi.lib.controllers.website.fetch_single_bangumi",
            return_value=WebsiteBangumi(id="badge-cover", name=bangumi_name, update_day="Mon", cover=cover_url),
        ) as fetch_single_bangumi,
        mock.patch("bgmi.lib.controllers.ScriptRunner") as script_runner,
        mock.patch("bgmi.lib.controllers.download_cover") as download_cover,
    ):
        script_runner.return_value.get_models_dict.return_value = []

        cal(cover=[])

    fetch_single_bangumi.assert_called_once()
    download_cover.assert_called_once_with([cover_url])
    assert Bangumi.get(Bangumi.name == bangumi_name).cover == cover_url
