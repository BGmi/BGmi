import datetime

import pytest
from starlette.testclient import TestClient

from bgmi.front.server import make_app
from bgmi.lib.table import Bangumi, Followed, Session

client = TestClient(make_app(debug=True))


@pytest.fixture()
def _calendar_data():
    with Session.begin() as tx:
        tx.query(Bangumi).delete()
        tx.query(Followed).delete()

        today_day = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[datetime.date.today().weekday()]

        tx.add(Bangumi(name="TestAnime1", id="t1", update_day=today_day))
        tx.add(Bangumi(name="TestAnime2", id="t2", update_day="Unknown"))
        tx.add(Followed(bangumi_name="TestAnime1", episodes={1, 2}, status=Followed.STATUS_FOLLOWED))
        tx.add(
            Followed(
                bangumi_name="TestAnime2",
                episodes={1},
                status=Followed.STATUS_UPDATED,
                updated_time=int(datetime.datetime.now().timestamp()),
            )
        )


@pytest.mark.usefixtures("_calendar_data")
def test_calendar_ics_basic():
    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200
    body = r.text
    assert "BEGIN:VCALENDAR" in body
    assert "TestAnime1" in body
    # Unknown update_day should be excluded
    assert "TestAnime2" not in body


@pytest.mark.usefixtures("_calendar_data")
def test_calendar_ics_today_date():
    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200
    body = r.text
    today_str = datetime.date.today().strftime("%Y%m%d")
    assert today_str in body


@pytest.mark.usefixtures("_calendar_data")
def test_calendar_ics_type_download():
    r = client.get("/resource/calendar.ics?type=download")
    assert r.status_code == 200
    body = r.text
    assert "BEGIN:VCALENDAR" in body
    # TestAnime2 has STATUS_UPDATED, should appear
    assert "Updated: TestAnime2" in body
    # TestAnime1 has STATUS_FOLLOWED, should not appear
    assert "Updated: TestAnime1" not in body


@pytest.mark.usefixtures("_calendar_data")
def test_calendar_ics_no_followed():
    with Session.begin() as tx:
        tx.query(Followed).delete()

    r = client.get("/resource/calendar.ics")
    assert r.status_code == 200
    body = r.text
    assert "BEGIN:VCALENDAR" in body
    assert "BEGIN:VEVENT" not in body
