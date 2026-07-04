import datetime
from collections import defaultdict

from icalendar import Calendar, Event
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from bgmi.lib.table import Followed, Scripts

# Map BANGUMI_UPDATE_TIME day names to Python weekday() values (Mon=0 .. Sun=6)
_DAY_TO_WEEKDAY = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


class CalendarHandler(HTTPEndpoint):
    @staticmethod
    def get(requests: Request) -> PlainTextResponse:
        type_ = requests.query_params.get("type", None)

        cal = Calendar()
        cal.add("prodid", "-//BGmi Followed Bangumi Calendar//bangumi.ricterz.me//")
        cal.add("version", "2.0")

        data = [
            {"update_day": b.update_day, "bangumi_name": b.name, "status": f.status}
            for f, b in Followed.get_all_followed()
        ]

        for s in Scripts.all():
            data.append({"update_day": s.update_day, "bangumi_name": s.bangumi_name, "status": s.status})

        if type_ is None:
            bangumi_by_weekday: defaultdict[int, list[str]] = defaultdict(list)

            for j in data:
                wd = _DAY_TO_WEEKDAY.get(j["update_day"])
                if wd is not None:
                    bangumi_by_weekday[wd].append(j["bangumi_name"])

            today = datetime.date.today()
            today_weekday = today.weekday()
            for i in range(7):
                wd = (today_weekday + i) % 7
                if wd in bangumi_by_weekday:
                    for name in bangumi_by_weekday[wd]:
                        event = Event()
                        event.add("summary", name)
                        event_date = today + datetime.timedelta(days=i)
                        event.add("dtstart", event_date)
                        event.add("dtend", event_date)
                        cal.add_component(event)
        else:
            for d in data:
                if d["status"] == Followed.STATUS_UPDATED:
                    event = Event()
                    event.add("summary", "Updated: {}".format(d["bangumi_name"]))
                    event.add("dtstart", datetime.date.today())
                    event.add("dtend", datetime.date.today())
                    cal.add_component(event)

        cal.add("name", "Bangumi Calendar")
        cal.add("X-WR-CALNAM", "Bangumi Calendar")
        cal.add("description", "Followed Bangumi Calendar")
        cal.add("X-WR-CALDESC", "Followed Bangumi Calendar")

        return PlainTextResponse(cal.to_ical())
