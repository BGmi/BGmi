import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Type, TypeVar

import sqlalchemy as sa
from sqlalchemy import CHAR, Column, Integer, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, sessionmaker

from bgmi.config import cfg
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

# engine = create_engine(f"sqlite:///{cfg.db_path.as_posix()}")
engine = create_engine("sqlite:///./tmp/bangumi.db")

Session = sessionmaker(engine, expire_on_commit=False)

T = TypeVar("T")


class NotFoundError(Exception):
    def __init__(self, cls):
        super().__init__(f"{cls} not found")


class Base(DeclarativeBase):
    NotFoundError = NotFoundError

    @classmethod
    def get(cls: Type[T], *where: Any) -> T:
        with Session.begin() as session:
            o = session.scalar(sa.select(cls).where(*where).limit(1))
            if not o:
                raise NotFoundError(cls)
            return o

    def save(self) -> None:
        with Session.begin() as session:
            session.add(self)


metadata = Base.metadata
if os.environ.get("DEV"):
    print(f"using database {cfg.db_path}")


class Bangumi(Base):
    __tablename__ = "bangumi"

    id: Mapped[int] = Column(Integer, primary_key=True)  # type: ignore
    name: Mapped[str] = Column(Text, nullable=False, unique=True)  # type: ignore
    subtitle_group: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    keyword: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    update_time: Mapped[str] = Column(CHAR(5), nullable=False)  # type: ignore
    cover: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    status: Mapped[int] = Column(Integer, nullable=False)  # type: ignore

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
                sa.update(cls)
                .where(cls.name.not_in([x.bangumi_name for x in un_updated_bangumi]))
                .values(status=STATUS_END)
            )

    @classmethod
    def get_updating_bangumi(
        cls,
        status: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if status is None:
            sql = (
                sa.select(cls, Followed.status, Followed.episode)
                .outerjoin(Followed, cls.name == Followed.bangumi_name)
                .where(cls.status == STATUS_UPDATING)
            )
        else:
            sql = (
                sa.select(cls, Followed.status, Followed.episode)
                .outerjoin(Followed, cls.name == Followed.bangumi_name)
                .where((cls.status == STATUS_UPDATING) & (Followed.status == status))
            )

        with Session() as session:
            # if status is None:
            data = session.scalars(sql).all()

        weekly_list = defaultdict(list)
        for bangumi_item in data:
            weekly_list[bangumi_item.update_time.lower()].append(bangumi_item.__dict__)

        return weekly_list

    @classmethod
    def fuzzy_get(cls, name: str) -> "Bangumi":
        return cls.get(cls.name.contains(name))


class Followed(Base):
    __tablename__ = "followed"

    id: Mapped[int] = Column(Integer, primary_key=True)  # type: ignore
    bangumi_name: Mapped[str] = Column(Text, nullable=False, unique=True)  # type: ignore
    episode: Mapped[int] = Column(Integer, default=0, server_default="0")  # type: ignore
    status: Mapped[int] = Column(Integer)  # type: ignore
    updated_time: Mapped[int] = Column(Integer, default=0, server_default="0")  # type: ignore

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
        cls: Type["Followed"], status: int = STATUS_DELETED, bangumi_status: int = STATUS_UPDATING
    ) -> List["Followed"]:
        sql = (
            sa.select(Followed)
            .join(Bangumi, cls.bangumi_name == Bangumi.name)
            .where(cls.status.isnot(status), Bangumi.status == bangumi_status)
            .order_by(cls.updated_time.desc())
        )

        with Session() as s:
            return list(s.scalars(sql))


class Download(Base):
    __tablename__ = "download"

    id: Mapped[int] = Column(Integer, primary_key=True)  # type: ignore
    name: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    title: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    episode: Mapped[int] = Column(Integer, nullable=False)  # type: ignore
    download: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    status: Mapped[int] = Column(Integer, nullable=False)  # type: ignore

    @classmethod
    def get_all_downloads(cls, status: Optional[int] = None) -> List[dict]:
        with Session.begin() as session:
            if status is None:
                sql = sa.select(cls).where().order_by(cls.status)
            else:
                sql = sa.select(cls).where(cls.status == status).order_by(cls.status)

            return [x.__dict__ for x in session.scalars(sql)]

    def downloaded(self) -> None:
        self.status = STATUS_DOWNLOADED
        self.save()


class Filter(Base):
    __tablename__ = "filter"

    id: Mapped[int] = Column(Integer, primary_key=True)  # type: ignore
    bangumi_name: Mapped[str] = Column(Text, nullable=False, unique=True)  # type: ignore
    subtitle: Mapped[str] = Column(Text)  # type: ignore
    include: Mapped[str] = Column(Text)  # type: ignore
    exclude: Mapped[str] = Column(Text)  # type: ignore
    regex: Mapped[str] = Column(Text)  # type: ignore

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


class Subtitle(Base):
    __tablename__ = "subtitle"

    id: Mapped[str] = Column(Text, primary_key=True)  # type: ignore
    name: Mapped[str] = Column(Text, nullable=False)  # type: ignore

    @classmethod
    def get_subtitle_by_id(cls, id_list: List[str]) -> List["Subtitle"]:
        with Session.begin() as session:
            return [x for x in session.scalars(sa.select(cls).where(cls.id.in_(id_list)))]

    @classmethod
    def get_subtitle_by_name(cls, name_list: List[str]) -> List["Subtitle"]:
        with Session.begin() as session:
            return [x for x in session.scalars(sa.select(cls).where(cls.name.in_(name_list)))]


class Scripts(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = Column(Integer, primary_key=True)  # type: ignore
    bangumi_name: Mapped[str] = Column(Text, nullable=False, unique=True)  # type: ignore
    episode: Mapped[int] = Column(Integer, nullable=False)  # type: ignore
    status: Mapped[int] = Column(Integer, nullable=False)  # type: ignore
    updated_time: Mapped[int] = Column(Integer, nullable=False)  # type: ignore


def recreate_source_relatively_table() -> None:
    with Session.begin() as session:
        for table in [Subtitle, Filter, Download, Followed, Bangumi]:
            session.execute(sa.delete(table))


def recreate_scripts_table() -> None:
    with Session.begin() as session:
        for table in [
            Scripts,
        ]:
            session.execute(sa.delete(table))
