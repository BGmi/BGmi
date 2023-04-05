import os
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, TypeVar

import peewee
import sqlalchemy as sa
from peewee import FixedCharField, IntegerField, TextField
from playhouse.shortcuts import model_to_dict
from sqlalchemy import CHAR, Column, Integer, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, sessionmaker

from bgmi.config import cfg
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

db = peewee.SqliteDatabase(cfg.db_path)

# engine = create_engine(f"sqlite:///{cfg.db_path.as_posix()}")
engine = create_engine("sqlite:///./tmp/bangumi.db")

Session = sessionmaker(engine, expire_on_commit=False)

T = TypeVar("T")


class NotFoundError(Exception):
    ...


class Base(DeclarativeBase):
    @classmethod
    def get(cls: Type[T], *where: Any) -> T:
        with Session.begin() as session:
            o = session.scalar(sa.select(cls).where(*where).limit(1))
            if not o:
                raise NotFoundError()
            return o

    def save(self):
        with Session.begin() as session:
            session.add(self)


metadata = Base.metadata
if os.environ.get("DEV"):
    print(f"using database {cfg.db_path}")


class NeoDB(peewee.Model):
    DoesNotExist: Type[peewee.DoesNotExist]

    class Meta:
        database = db

    @classmethod
    def get(cls: Type[T], *query: Any, **filters: Any) -> T:
        return super().get(*query, **filters)  # type: ignore

    @classmethod
    def get_or_create(cls: Type[T], **kwargs: Any) -> Tuple[T, bool]:
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

    @staticmethod
    def serialize_subtitle_group(subtitle_group: Any) -> str:
        s = []

        if isinstance(subtitle_group, list):
            for sub in subtitle_group:
                if isinstance(sub, str):
                    s.append(sub)
                elif isinstance(sub, dict):
                    s.append(sub["id"])
                else:
                    s.append(sub.id)
        else:
            return str(subtitle_group)

        return ", ".join(sorted(s))

    @classmethod
    def delete_all(cls) -> None:
        with Session.begin() as session:
            un_updated_bangumi: List[Followed] = list(
                session.scalars(
                    sa.select(Followed).where(Followed.updated_time > (int(time.time()) - 2 * 7 * 24 * 3600))
                )
            )

            if os.getenv("DEBUG"):  # pragma: no cover
                print("ignore updating bangumi", [x.bangumi_name for x in un_updated_bangumi])

            # do not mark updating bangumi as STATUS_END
            session.execute(
                sa.update(SaBangumi)
                .where(SaBangumi.name.not_in([x.bangumi_name for x in un_updated_bangumi]))
                .values(status=STATUS_END)
            )

    @classmethod
    def get_updating_bangumi(
        cls,
        status: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if status is None:
            sql = (
                sa.select(SaBangumi, Followed.status, Followed.episode)
                .outerjoin(Followed, SaBangumi.name == Followed.bangumi_name)
                .where(SaBangumi.status == STATUS_UPDATING)
            )
        else:
            sql = (
                sa.select(SaBangumi, Followed.status, Followed.episode)
                .outerjoin(Followed, SaBangumi.name == Followed.bangumi_name)
                .where((SaBangumi.status == STATUS_UPDATING) & (Followed.status == status))
            )

        with Session() as session:
            # if status is None:
            data = session.scalars(sql).all()

        weekly_list = defaultdict(list)
        for bangumi_item in data:
            weekly_list[bangumi_item.update_time.lower()].append(bangumi_item.__dict__)

        return weekly_list

    @classmethod
    def fuzzy_get(cls, name: str) -> "SaBangumi":
        return SaBangumi.get(SaBangumi.name.contains(name))


class _Followed(NeoDB):
    bangumi_name = TextField(unique=True)
    episode = IntegerField(null=True, default=0)
    status = IntegerField(null=True)
    updated_time = IntegerField(null=True)

    class Meta:
        database = db
        table_name = "followed"


class SaBangumi(Base):
    __tablename__ = "bangumi"

    id = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(Text, nullable=False, unique=True)
    subtitle_group = Column(Text, nullable=False)
    keyword = Column(Text, nullable=False)
    update_time = Column(CHAR(5), nullable=False)
    cover = Column(Text, nullable=False)
    status: Mapped[int] = Column(Integer, nullable=False)


class Followed(Base):
    __tablename__ = "followed"

    id = Column(Integer, primary_key=True)
    bangumi_name = Column(Text, nullable=False, unique=True)
    episode = Column(Integer, default=0, server_default="0")
    status: Mapped[int] = Column(Integer)
    updated_time: Mapped[int] = Column(Integer, default=0, server_default="0")

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            bangumi_name: str,
            episode: int = 0,
            status: int,
            updated_time: int = 0,
            id: Optional[int] = id,
        ):
            ...

    @classmethod
    def delete_followed(cls, batch: bool = True) -> bool:
        if not batch:
            if not input("[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ") == "y":
                return False

        with Session.begin() as session:
            session.execute(sa.delete(cls))
        return True

    @classmethod
    def get_all_followed(
        cls: "Followed", status: int = STATUS_DELETED, bangumi_status: int = STATUS_UPDATING
    ) -> List["Followed"]:
        sql = (
            sa.select(cls)
            .join(SaBangumi, cls.bangumi_name == SaBangumi.name)
            .where(cls.status != status, SaBangumi.status == bangumi_status)
            .order_by(cls.updated_time.desc())
        )

        with Session() as s:
            return list(s.scalars(sql))


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
    subtitle = TextField(null=True)  # type: Optional[str]
    include = TextField(null=True)  # type: Optional[str]
    exclude = TextField(null=True)  # type: Optional[str]
    regex = TextField(null=True)  # type: Optional[str]

    @property
    def subtitle_group_split(self) -> List[str]:
        if self.subtitle:
            # pylint:disable=no-member
            return [x.strip() for x in self.subtitle.split(",")]
        else:
            return []

    def apply_on_episodes(self, result: List[Episode]) -> List[Episode]:
        if self.include:
            # pylint:disable=no-member
            include_list = [s.strip().lower() for s in self.include.split(",")]
            result = [e for e in result if e.contains_any_words(include_list)]

        if cfg.enable_global_include_keywords:
            include_list = [s.strip().lower() for s in cfg.global_include_keywords]
            result = [e for e in result if e.contains_any_words(include_list)]

        if self.exclude:
            # pylint:disable=no-member
            exclude_list = [s.strip().lower() for s in self.exclude.split(",")]
            result = [e for e in result if not e.contains_any_words(exclude_list)]

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


class Scripts(NeoDB):
    bangumi_name = TextField(null=False, unique=True)
    episode = IntegerField(default=0)
    status = IntegerField(default=0)
    updated_time = IntegerField(default=0)


def recreate_source_relatively_table() -> None:
    table_to_drop = [
        Subtitle,
        Filter,
        Download,
    ]  # type: List[Type[NeoDB]]
    for table in table_to_drop:
        table.delete().execute()  # pylint: disable=no-value-for-parameter

    with Session.begin() as session:
        session.execute(sa.delete(Followed))
        session.execute(sa.delete(SaBangumi))


def recreate_scripts_table() -> None:
    table_to_drop = [
        Scripts,
    ]  # type: List[Type[NeoDB]]
    for table in table_to_drop:
        table.delete().execute()  # pylint: disable=no-value-for-parameter
