import datetime
import os
from collections import defaultdict

from icalendar import Calendar, Event

from bgmi.config import SAVE_PATH
from bgmi.front.base import BaseHandler
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.models import Download, Followed


class BangumiHandler(BaseHandler):
    def get(self, _: str) -> None:
        if os.environ.get("DEV", False):  # pragma: no cover
            with open(os.path.join(SAVE_PATH, _), "rb") as f:
                self.write(f.read())
                self.finish()
        else:
            self.set_header("Content-Type", "text/html")
            self.write("<h1>BGmi HTTP Service</h1>")
            self.write(
                "<pre>Please modify your web server configure file\n"
                f"to server this path to '{SAVE_PATH}'.\n"
                "e.g.\n\n"
                "...\n"
                "autoindex on;\n"
                "location /bangumi {\n"
                f"    alias {SAVE_PATH};\n"
                "}\n"
                "...\n\n"
                "If use want to use Tornado to serve static files, please run\n"
                "<code>`bgmi config TORNADO_SERVE_STATIC_FILES 1`</code></pre>"
            )
            self.finish()


class RssHandler(BaseHandler):
    def get(self) -> None:
        data = Download.get_all_downloads()
        self.set_header("Content-Type", "text/xml")
        self.render("templates/download.xml", data=data)


class CalendarHandler(BaseHandler):
    def get(self) -> None:
        type_ = self.get_argument("type", None)

        cal = Calendar()
        cal.add("prodid", "-//BGmi Followed Bangumi Calendar//bangumi.ricterz.me//")
        cal.add("version", "2.0")

        data = Followed.get_all_followed()
        data.extend(self.patch_list)

        if type_ is None:

            bangumi = defaultdict(list)

            for j in data:
                bangumi[BANGUMI_UPDATE_TIME.index(j["update_time"]) + 1].append(
                    j["bangumi_name"]
                )

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

        self.write(cal.to_ical())
        self.finish()
