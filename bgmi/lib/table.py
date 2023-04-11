import os
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type, TypeVar

import sqlalchemy as sa
import sqlalchemy.event
from loguru import logger
from sqlalchemy import CHAR, Column, Integer, Row, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, sessionmaker

from bgmi.config import cfg
from bgmi.utils import episode_filter_regex
from bgmi.website.model import Episode

# subscription status

debug = os.getenv("DEBUG") in ["true", "True"]


def before_cursor_execute(
    _: Any, cursor: Any, statement: str, parameters: List[Any], *args: Any, **kwargs: Any
) -> None:
    logger.debug("executing sql {} {}", statement, parameters)
    if debug:
        print(statement, parameters)


engine = create_engine(f"sqlite:///{cfg.db_path.absolute().as_posix()}")
sqlalchemy.event.listen(engine, "before_cursor_execute", before_cursor_execute)
Session = sessionmaker(engine, expire_on_commit=False)


class NotFoundError(Exception):
    def __init__(self, cls: Type["Base"]) -> None:
        super().__init__(f"{cls} not found")


T = TypeVar("T", bound="Base")


class Base(DeclarativeBase):
    NotFoundError = NotFoundError

    @classmethod
    def get(cls: Type[T], *where: Any) -> T:
        with Session.begin() as session:
            o = session.scalar(sa.select(cls).where(*where).limit(1))
            if not o:
                raise NotFoundError(cls)
            return o

    @classmethod
    def all(cls: Type[T], *where: Any) -> List[T]:
        with Session.begin() as session:
            return list(session.scalars(sa.select(cls).where(*where)).all())

    def save(self, tx: Optional[sa.orm.Session] = None) -> None:
        if tx:
            tx.add(self)
            return

        with Session.begin() as session:
            session.add(self)


if os.environ.get("DEV"):
    print(f"using database {cfg.db_path}")


class Bangumi(Base):
    __tablename__ = "bangumi"
    STATUS_UPDATING = 0
    STATUS_END = 1

    id: Mapped[str] = Column(Text, primary_key=True, nullable=False)  # type: ignore

    name: Mapped[str] = Column(Text, nullable=False, unique=True)  # type: ignore
    subtitle_group: Mapped[List[str]] = Column(sa.JSON, nullable=False, default=[], server_default="[]")  # type: ignore
    update_day: Mapped[str] = Column(
        CHAR(5), nullable=False, default="Unknown", server_default="Unknown"
    )  # type: ignore
    cover: Mapped[str] = Column(Text, nullable=False, default="", server_default="")  # type: ignore
    status: Mapped[int] = Column(
        Integer, nullable=False, default=STATUS_UPDATING, server_default=str(STATUS_UPDATING)
    )  # type: ignore

    if TYPE_CHECKING:

        def __init__(
            self,
            id: str,
            name: str,
            update_day: str = "Unknown",
            subtitle_group: Optional[List[str]] = None,
            cover: str = "",
            status: int = STATUS_UPDATING,
        ):
            super().__init__()

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
                .values(status=cls.STATUS_END)
            )

    @classmethod
    def get_updating_bangumi(
        cls,
        status: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if status is None:
            where = cls.status == cls.STATUS_UPDATING
        else:
            where = (cls.status == cls.STATUS_UPDATING) & (Followed.status == status)

        with Session.begin() as session:
            data = (
                session.query(cls, Followed.status, Followed.episodes)
                .outerjoin(Followed, cls.name == Followed.bangumi_name)
                .where(where)
                .all()
            )

        weekly_list = defaultdict(list)
        for bangumi_item, followed_status, episode in data:
            weekly_list[bangumi_item.update_day.lower()].append(
                {**bangumi_item.__dict__, "status": followed_status, "episode": max(episode) if episode else None}
            )

        return weekly_list


class Followed(Base):
    __tablename__ = "followed"

    STATUS_DELETED = 0
    STATUS_FOLLOWED = 1
    STATUS_UPDATED = 2

    FOLLOWED_STATUS = (
        STATUS_DELETED,
        STATUS_FOLLOWED,
        STATUS_UPDATED,
    )

    bangumi_name: Mapped[str] = Column(Text, nullable=False, primary_key=True)  # type: ignore
    episodes: Mapped[List[int]] = Column(sa.JSON, nullable=False, default=[], server_default="[]")  # type: ignore
    status: Mapped[int] = Column(
        Integer, nullable=False, default=STATUS_UPDATED, server_default=str(STATUS_UPDATED)
    )  # type: ignore
    updated_time: Mapped[int] = Column(Integer, nullable=False, default=0, server_default="0")  # type: ignore
    subtitle: List[str] = Column(sa.JSON, nullable=False, default=[], server_default="[]")  # type: ignore
    include: Mapped[List[str]] = Column(sa.JSON, nullable=False, default=[], server_default="[]")  # type: ignore
    exclude: Mapped[List[str]] = Column(sa.JSON, nullable=False, default=[], server_default="[]")  # type: ignore
    regex: Mapped[str] = Column(Text, nullable=False, default="", server_default="")  # type: ignore

    is_script: Mapped[bool] = Column(sa.Boolean, nullable=False, default=False, server_default="0")  # type: ignore

    @property
    def episode(self) -> int:
        if self.episodes:
            return max(self.episodes)  # type: ignore
        return 0

    @classmethod
    def delete_followed(cls, batch: bool = True) -> bool:
        if not batch and input("[+] are you sure want to CLEAR ALL THE BANGUMI? (y/N): ") != "y":
            return False

        with Session.begin() as session:
            session.execute(sa.delete(cls))
        return True

    @classmethod
    def get_all_followed(
        cls: Type["Followed"], bangumi_status: int = Bangumi.STATUS_UPDATING
    ) -> List[Row[Tuple["Followed", "Bangumi"]]]:
        with Session() as tx:
            return list(
                tx.query(Followed, Bangumi)
                .join(Bangumi, cls.bangumi_name == Bangumi.name)
                .where(cls.status.isnot(cls.STATUS_DELETED), Bangumi.status == bangumi_status)
                .order_by(cls.updated_time.desc())
                .all()
            )

    def apply_on_episodes(self, result: List[Episode]) -> List[Episode]:
        if self.include:
            # pylint:disable=no-member
            include_list = [s.strip().lower() for s in self.include]
            result = [e for e in result if e.contains_any_words(include_list)]

        if cfg.enable_global_include_keywords:
            include_list = [s.strip().lower() for s in cfg.global_include_keywords]
            result = [e for e in result if e.contains_any_words(include_list)]

        if self.exclude:
            # pylint:disable=no-member
            exclude_list = [s.strip().lower() for s in self.exclude]
            result = [e for e in result if not e.contains_any_words(exclude_list)]

        return episode_filter_regex(data=result, regex=self.regex)

    def save(self, tx: Optional[sa.orm.Session] = None) -> None:
        self.episodes = sorted(set(self.episodes))
        super().save(tx)


class Download(Base):
    __tablename__ = "download"

    STATUS_NOT_DOWNLOAD = 0
    STATUS_DOWNLOADING = 1
    STATUS_DOWNLOADED = 2

    id: Mapped[int] = Column(Integer, nullable=False, primary_key=True)  # type: ignore
    bangumi_name: Mapped[str] = Column("name", Text, nullable=False)  # type: ignore
    title: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    episode: Mapped[int] = Column(Integer, nullable=False)  # type: ignore
    download: Mapped[str] = Column(Text, nullable=False)  # type: ignore
    status: Mapped[int] = Column(Integer, nullable=False)  # type: ignore

    if TYPE_CHECKING:

        def __init__(
            self,
            bangumi_name: str,
            title: str,
            episode: int,
            download: str,
            status: int,
            id: Optional[int] = None,
        ):
            super().__init__()

    @classmethod
    def get_all_downloads(cls, status: Optional[int] = None) -> List["Download"]:
        with Session.begin() as session:
            if status is None:
                sql = sa.select(cls).where().order_by(cls.status)
            else:
                sql = sa.select(cls).where(cls.status == status).order_by(cls.status)

            return list(session.scalars(sql).all())

    def downloaded(self) -> None:
        self.status = self.STATUS_DOWNLOADED
        self.save()


class Subtitle(Base):
    __tablename__ = "subtitle"

    id: Mapped[str] = Column(Text, nullable=False, primary_key=True)  # type: ignore
    name: Mapped[str] = Column(Text, nullable=False)  # type: ignore

    @classmethod
    def get_subtitle_by_id(cls, id_list: List[str]) -> List["Subtitle"]:
        with Session.begin() as session:
            return list(session.scalars(sa.select(cls).where(cls.id.in_(id_list))))

    @classmethod
    def get_subtitle_by_name(cls, name_list: List[str]) -> List["Subtitle"]:
        with Session.begin() as session:
            return list(session.scalars(sa.select(cls).where(cls.name.in_(name_list))))


class Scripts(Base):
    __tablename__ = "scripts"

    bangumi_name: Mapped[str] = Column(Text, primary_key=True, nullable=False, unique=True)  # type: ignore
    episodes: Mapped[List[str]] = Column(sa.JSON, nullable=False, default=[], server_default="[]")  # type: ignore
    status: Mapped[int] = Column(Integer, nullable=False)  # type: ignore
    updated_time: Mapped[int] = Column(Integer, nullable=False, default=0, server_default="0")  # type: ignore
    update_day: Mapped[str] = Column(Text, nullable=False, default="Unknown", server_default="Unknown")  # type: ignore
    cover: Mapped[str] = Column(Text, nullable=False, default="", server_default="")  # type: ignore

    def save(self, tx: Optional[sa.orm.Session] = None) -> None:
        self.episodes = sorted(set(self.episodes))
        super().save(tx)


def recreate_source_relatively_table() -> None:
    with Session.begin() as session:
        for table in [Subtitle, Download, Followed, Bangumi]:
            session.execute(sa.delete(table))


def recreate_scripts_table() -> None:
    with Session.begin() as session:
        for table in [
            Scripts,
        ]:
            session.execute(sa.delete(table))
