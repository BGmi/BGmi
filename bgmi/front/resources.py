import datetime
from collections import defaultdict

from icalendar import Calendar, Event
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.table import Followed, Scripts


class CalendarHandler(HTTPEndpoint):
    @staticmethod
    def get(requests: Request) -> PlainTextResponse:
        type_ = requests.query_params.get("type", None)

        cal = Calendar()
        cal.add("prodid", "-//BGmi Followed Bangumi Calendar//bangumi.ricterz.me//")
        cal.add("version", "2.0")

        data = [{"update_day": b.update_day, "bangumi_name": b.name} for f, b in Followed.get_all_followed()]

        for s in Scripts.all():
            data.append({"update_day": s.update_day, "bangumi_name": s.bangumi_name})

        if type_ is None:
            bangumi = defaultdict(list)

            for j in data:
                bangumi[BANGUMI_UPDATE_TIME.index(j["update_day"]) + 1].append(j["bangumi_name"])

            weekday = datetime.datetime.now().weekday()
            for i, k in enumerate(range(weekday, weekday + 7)):
                if k % 7 in bangumi:
                    for v in bangumi[k % 7]:
                        event = Event()
                        event.add("summary", v)
                        event.add(
                            "dtstart",
                            datetime.datetime.now().date() + datetime.timedelta(i - 1),
                        )
                        event.add(
                            "dtend",
                            datetime.datetime.now().date() + datetime.timedelta(i - 1),
                        )
                        cal.add_component(event)
        else:
            data = [bangumi for bangumi in data if bangumi["status"] == 2]
            for d in data:
                event = Event()
                event.add("summary", "Updated: {}".format(d["bangumi_name"]))
                event.add("dtstart", datetime.datetime.now().date())
                event.add("dtend", datetime.datetime.now().date())
                cal.add_component(event)

        cal.add("name", "Bangumi Calendar")
        cal.add("X-WR-CALNAM", "Bangumi Calendar")
        cal.add("description", "Followed Bangumi Calendar")
        cal.add("X-WR-CALDESC", "Followed Bangumi Calendar")

        return PlainTextResponse(cal.to_ical())
