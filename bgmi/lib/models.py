import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

import peewee
from peewee import FixedCharField, IntegerField, TextField
from playhouse.shortcuts import model_to_dict

import bgmi.config
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.utils import episode_filter_regex
from bgmi.website.model import Episode

# bangumi status
STATUS_UPDATING = 0
STATUS_END = 1
BANGUMI_STATUS = (STATUS_UPDATING, STATUS_END)

# subscription status
STATUS_DELETED = 0
STATUS_FOLLOWED = 1
STATUS_UPDATED = 2
FOLLOWED_STATUS = (STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED)

# download status
STATUS_NOT_DOWNLOAD = 0
STATUS_DOWNLOADING = 1
STATUS_DOWNLOADED = 2
DOWNLOAD_STATUS = (STATUS_NOT_DOWNLOAD, STATUS_DOWNLOADING, STATUS_DOWNLOADED)

DoesNotExist = peewee.DoesNotExist

db = peewee.SqliteDatabase(bgmi.config.DB_PATH)

if os.environ.get("DEV"):
    print("using", bgmi.config.DB_PATH)


_Cls = TypeVar("_Cls")


class NeoDB(peewee.Model):
    class Meta:
        database = db

    @classmethod
    def get(cls: Type[_Cls], *query: Any, **filters: Any) -> _Cls:
        return super().get(*query, **filters)  # type: ignore

    @classmethod
    def get_or_create(cls: Type[_Cls], **kwargs: Any) -> Tuple[_Cls, bool]:
        return super().get_or_create(**kwargs)  # type: ignore


class Bangumi(NeoDB):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True, null=False)
    subtitle_group = TextField(null=False)
    keyword = TextField()
    update_time = FixedCharField(5, null=False)
    cover = TextField()
    status = IntegerField(default=0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        update_time = kwargs.get("update_time", "").title()
        if update_time and update_time not in BANGUMI_UPDATE_TIME:
            raise ValueError(f"unexpected update time {update_time}")
        self.update_time = update_time
        if isinstance(kwargs.get("subtitle_group"), list):
            s = []
            for sub in kwargs["subtitle_group"]:
                if isinstance(sub, str):
                    s.append(sub)
                elif isinstance(sub, dict):
                    s.append(sub["id"])
                else:
                    s.append(sub.id)
            self.subtitle_group = ", ".join(sorted(s))

    @classmethod
    def delete_all(cls) -> None:
        un_updated_bangumi = Followed.select().where(
            Followed.updated_time > (int(time.time()) - 2 * 7 * 24 * 3600)
        )  # type: List[Followed]
        if os.getenv("DEBUG"):  # pragma: no cover
            print(
                "ignore updating bangumi", [x.bangumi_name for x in un_updated_bangumi]
            )

        cls.update(status=STATUS_END).where(
            cls.name.not_in([x.bangumi_name for x in un_updated_bangumi])
        ).execute()  # do not mark updating bangumi as STATUS_END

    @classmethod
    def get_updating_bangumi(
        cls, status: Optional[int] = None, order: bool = True
    ) -> Any:
        if status is None:
            data = (
                cls.select(Followed.status, Followed.episode, cls)
                .join(
                    Followed,
                    peewee.JOIN["LEFT_OUTER"],
                    on=(cls.name == Followed.bangumi_name),
                )
                .where(cls.status == STATUS_UPDATING)
                .dicts()
            )
        else:
            data = (
                cls.select(Followed.status, Followed.episode, cls)
                .join(
                    Followed,
                    peewee.JOIN["LEFT_OUTER"],
                    on=(cls.name == Followed.bangumi_name),
                )
                .where((cls.status == STATUS_UPDATING) & (Followed.status == status))
                .dicts()
            )

        if order:
            weekly_list = defaultdict(list)
            for bangumi_item in data:
                weekly_list[bangumi_item["update_time"].lower()].append(
                    dict(bangumi_item)
                )
        else:
            weekly_list = list(data)  # type: ignore

        return weekly_list

    @classmethod
    def fuzzy_get(cls, **filters: Any) -> "Bangumi":
        fuzzy_q = []
        raw_q = []
        for key, value in filters.items():
            raw_q.append(getattr(cls, key) == value)
            fuzzy_q.append(getattr(cls, key).contains(value))

        raw = list(cls.select().where(*raw_q))  # type: List[Bangumi]
        if raw:
            return raw[0]

        fuzzy = list(cls.select().where(*fuzzy_q))  # type: List[Bangumi]
        if fuzzy:
            return fuzzy[0]

        raise cls.DoesNotExist


class Followed(NeoDB):
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)

    class Meta:
        database = db
        table_name = "followed"

    @classmethod
    def delete_followed(cls, batch: bool = True) -> bool:
        q = cls.delete()
        if not batch:
            if (
                not input("[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ")
                == "y"
            ):
                return False

        q.execute()
        return True

    @classmethod
    def get_all_followed(
        cls, status: int = STATUS_DELETED, bangumi_status: int = STATUS_UPDATING
    ) -> List[dict]:
        join_cond = Bangumi.name == cls.bangumi_name
        d = (
            cls.select(Bangumi.name, Bangumi.update_time, Bangumi.cover, cls)
            .join(Bangumi, peewee.JOIN["LEFT_OUTER"], on=join_cond)
            .where((cls.status != status) & (Bangumi.status == bangumi_status))
            .order_by(cls.updated_time.desc())
            .dicts()
        )

        return list(d)


class Download(NeoDB):
    name = TextField(null=False)
    title = TextField(null=False)
    episode = IntegerField(default=0)
    download = TextField()
    status = IntegerField(default=0)

    @classmethod
    def get_all_downloads(cls, status: Optional[int] = None) -> List[dict]:
        if status is None:
            data = list(cls.select().order_by(cls.status))
        else:
            data = list(cls.select().where(cls.status == status).order_by(cls.status))

        for index, x in enumerate(data):
            data[index] = model_to_dict(x)
        return data

    def downloaded(self) -> None:
        self.status = STATUS_DOWNLOADED
        self.save()


class Filter(NeoDB):
    bangumi_name = TextField(unique=True)  # type: Optional[str]
    subtitle = TextField()  # type: Optional[str]
    include = TextField()  # type: Optional[str]
    exclude = TextField()  # type: Optional[str]
    regex = TextField()  # type: Optional[str]

    @property
    def subtitle_group_split(self) -> List[str]:
        if self.subtitle:
            return [x.strip() for x in self.subtitle.split(",")]
        else:
            return []

    def apply_on_episodes(self, result: List[Episode]) -> List[Episode]:
        if self.include:
            include_list = list(map(lambda s: s.strip(), self.include.split(",")))
            result = list(
                filter(
                    lambda s: True
                    if all(map(lambda t: t in s.title, include_list))
                    else False,
                    result,
                )
            )

        if self.exclude:
            exclude_list = list(map(lambda s: s.strip(), self.exclude.split(",")))
            result = list(
                filter(
                    lambda s: True
                    if all(map(lambda t: t not in s.title, exclude_list))
                    else False,
                    result,
                )
            )

        return episode_filter_regex(data=result, regex=self.regex)


class Subtitle(NeoDB):
    id = TextField(primary_key=True, unique=True)
    name = TextField()

    @classmethod
    def get_subtitle_by_id(cls, id_list: List[str]) -> List[Dict[str, str]]:
        data = list(cls.select().where(cls.id.in_(id_list)))
        for index, subtitle in enumerate(data):
            data[index] = model_to_dict(subtitle)
        return data

    @classmethod
    def get_subtitle_by_name(cls, name_list: List[str]) -> List[Dict[str, str]]:
        data = list(cls.select().where(cls.name.in_(name_list)))
        for index, subtitle in enumerate(data):
            data[index] = model_to_dict(subtitle)
        return data


script_db = peewee.SqliteDatabase(bgmi.config.SCRIPT_DB_PATH)


class Scripts(peewee.Model):
    bangumi_name = TextField(null=False, unique=True)
    episode = IntegerField(default=0)
    status = IntegerField(default=0)
    updated_time = IntegerField(default=0)

    class Meta:
        database = script_db


def recreate_source_relatively_table() -> None:
    table_to_drop = [
        Bangumi,
        Followed,
        Subtitle,
        Filter,
        Download,
    ]  # type: List[Type[NeoDB]]
    for table in table_to_drop:
        table.delete().execute()


if __name__ == "__main__":  # pragma:no cover
    from pprint import pprint

    d = Bangumi.get_updating_bangumi(status=STATUS_FOLLOWED)
    pprint(d)
