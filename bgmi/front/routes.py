from typing import Any, Dict, Generic, List, Optional, TypeVar

import fastapi
from pydantic import BaseModel
from pydantic.generics import GenericModel
from starlette.exceptions import HTTPException

from bgmi import __version__
from bgmi.config import cfg
from bgmi.front.index import get_player
from bgmi.lib import table
from bgmi.lib.table import Followed, NotFoundError, Scripts, Session
from bgmi.utils import normalize_path

app = fastapi.FastAPI(docs_url="/")

COVER_URL = "/bangumi/cover"
WEEK = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class Player(BaseModel):
    path: str


T = TypeVar("T")


class Response(GenericModel, Generic[T]):
    version: str
    danmaku_api: str
    data: T


def jsonify(data: Any) -> Dict[str, Any]:
    return {
        "version": __version__,
        "danmaku_api": cfg.http.danmaku_api_url,
        "data": data,
    }


class Bangumi(BaseModel):
    status: int
    episode: int
    cover: str
    bangumi_name: str
    updated_time: int
    player: Dict[int, Player]


@app.get("/{t}", response_model=Response[List[Bangumi]])
def bangumi_list(t: str) -> Any:
    if t not in (
        "old",
        "index",
    ):
        raise HTTPException(404)

    bangumi_status = table.Bangumi.STATUS_UPDATING
    if t == "old":
        bangumi_status = table.Bangumi.STATUS_END

    data: List[Dict[str, Any]] = [
        {
            key: value
            for key, value in {
                **bangumi.__dict__,
                **followed.__dict__,
                "cover": f"{COVER_URL}/{normalize_path(bangumi.cover)}",
            }.items()
            if not key.startswith("_")
        }
        for followed, bangumi in Followed.get_all_followed(bangumi_status=bangumi_status)
    ]

    def sorter(_: Dict[str, int]) -> int:
        return _["updated_time"] if _["updated_time"] else 1

    if t == "index":
        with Session.begin() as tx:
            patch_list = tx.query(Scripts).where(Scripts.status.isnot(Followed.STATUS_DELETED)).all()
            for s in patch_list:
                data.append(
                    {
                        "bangumi_name": s.bangumi_name,
                        "updated_time": s.updated_time,
                        "status": s.status,
                        "cover": s.cover,
                        "episode": s.episode,
                    }
                )
        data.sort(key=sorter)

    data.reverse()

    for item in data:
        item["player"] = get_player(item["bangumi_name"])

    return jsonify(data)


async def auth_header(
    token: Optional[str] = fastapi.Header(None, alias="authorization", example="Bearer {token}")
) -> Any:
    if not token:
        raise fastapi.HTTPException(401, "missing http header authorization")

    if not token.startswith("Bearer "):
        raise fastapi.HTTPException(401, "bad authorization header, should be `Bearer {token}`")
    if token[7:] == cfg.http.admin_token:
        return
    raise fastapi.HTTPException(401, "wrong auth token")


admin = fastapi.APIRouter(
    dependencies=[fastapi.Depends(auth_header)], responses={401: {"description": "wrong api token"}}
)


@admin.post(
    "/add",
    responses={
        200: {"description": "成功添加"},
        404: {"description": "番剧不存在"},
    },
)
def add(bangumi: str = fastapi.Body(embed=True)) -> Any:
    try:
        b = table.Bangumi.get(table.Bangumi.name == bangumi)
    except table.Bangumi.NotFoundError:
        raise HTTPException(404, "Bangumi not exist")

    with Session.begin() as tx:
        f = tx.query(table.Followed).where(table.Followed.bangumi_name == b.name).scalar()
        if f:
            f.status = table.Followed.STATUS_FOLLOWED
            tx.add(f)
        else:
            tx.add(table.Followed(bangumi_name=b.name, episode=0, status=table.Followed.STATUS_FOLLOWED))

    return {}


@admin.post(
    "/mark",
    responses={
        200: {"description": "成功修改"},
        404: {"description": "番剧不存在或者未订阅"},
    },
)
def mark(bangumi: str = fastapi.Body(embed=True), episode: int = fastapi.Body(embed=True)) -> Any:
    with Session.begin() as tx:
        f: Optional[table.Followed] = tx.query(table.Followed).where(table.Followed.bangumi_name == bangumi).scalar()
        if f is None:
            raise HTTPException(404, "bangumi not exists or not followed")
        f.episode = episode
        tx.add(f)

    return {}


@admin.post(
    "/delete",
    responses={
        200: {"description": "成功删除"},
        404: {"description": "番剧不存在或者未订阅"},
    },
)
def delete(bangumi: str = fastapi.Body(embed=True)) -> Any:
    with Session.begin() as tx:
        f: Optional[table.Followed] = (
            tx.query(table.Followed)
            .where(table.Followed.bangumi_name == bangumi, table.Followed.status.isnot(table.Followed.STATUS_DELETED))
            .scalar()
        )
        if f is None:
            raise HTTPException(404, "bangumi not exists or not followed")
        f.status = table.Followed.STATUS_DELETED
        tx.add(f)

    return {}


class Filter(BaseModel):
    available_subtitle: List[str]
    selected_subtitle: List[str]
    include: List[str]
    exclude: List[str]
    regex: str


@admin.get(
    "/filter/{bangumi}",
    responses={
        200: {"description": "成功"},
        404: {"description": "番剧不存在或者未订阅"},
    },
)
def get_filter(bangumi: str = fastapi.Path()) -> Any:
    try:
        f = table.Followed.get(
            table.Followed.bangumi_name == bangumi, table.Followed.status.isnot(table.Followed.STATUS_DELETED)
        )
    except NotFoundError:
        raise HTTPException(404, "bangumi not followed")

    try:
        b = table.Bangumi.get(table.Bangumi.name == bangumi)
    except NotFoundError:
        raise HTTPException(404, "bangumi not exists")

    available_subtitle = table.Subtitle.get_subtitle_by_id(b.subtitle_group)

    return {
        "available_subtitle": [x.name for x in available_subtitle],
        "selected_subtitle": [x.name for x in table.Subtitle.get_subtitle_by_id(f.subtitle)],
        "include": f.include,
        "exclude": f.exclude,
        "regex": f.regex,
    }


@admin.patch(
    "/filter/{bangumi}",
    responses={
        200: {"description": "成功"},
        400: {"description": "字幕组不可用"},
        404: {"description": "番剧不存在或者未订阅"},
    },
)
def update_filter(
    bangumi: str = fastapi.Path(),
    selected_subtitle: Optional[List[str]] = fastapi.Body(None, embed=True),
    include: Optional[List[str]] = fastapi.Body(None, embed=True),
    exclude: Optional[List[str]] = fastapi.Body(None, embed=True),
    regex: Optional[str] = fastapi.Body(None, embed=True),
) -> Any:
    try:
        f = table.Followed.get(
            table.Followed.bangumi_name == bangumi, table.Followed.status.isnot(table.Followed.STATUS_DELETED)
        )
    except NotFoundError:
        raise HTTPException(404, "bangumi not followed")

    try:
        b = table.Bangumi.get(
            table.Bangumi.name == bangumi,
        )
    except NotFoundError:
        raise HTTPException(404, "bangumi not exists")

    if selected_subtitle is not None:
        available_subtitle = {x.name: x.id for x in table.Subtitle.get_subtitle_by_id(b.subtitle_group)}
        selected = []
        for s in selected_subtitle:
            if s not in available_subtitle:
                raise HTTPException(404, f"字幕组 {s} 不可用")
            selected.append(s)

        f.subtitle = [x.id for x in table.Subtitle.get_subtitle_by_name(f.subtitle)]

    if include is not None:
        f.include = include
    if exclude is not None:
        f.exclude = exclude
    if regex is not None:
        f.regex = regex

    f.save()

    return {}


class CalendarItem(BaseModel):
    id: str
    cover: str
    name: str
    update_day: str
    status: Optional[int]
    episode: Optional[int]


class Calendar(BaseModel):
    sat: Optional[List[CalendarItem]]
    sun: Optional[List[CalendarItem]]
    mon: Optional[List[CalendarItem]]
    tue: Optional[List[CalendarItem]]
    thu: Optional[List[CalendarItem]]
    wed: Optional[List[CalendarItem]]
    fri: Optional[List[CalendarItem]]


@admin.get(
    "/calendar",
    responses={
        200: {"description": "成功"},
        404: {"description": "暂无番剧，请使用命令行更新calendar"},
    },
    response_model=Calendar,
)
def calendar() -> Any:
    print("calendar router")
    weekly_list = table.Bangumi.get_updating_bangumi()
    if not weekly_list:
        raise HTTPException(404, '请使用 "bgmi cal -f" 命令更新番剧列表')

    return weekly_list


app.include_router(admin, prefix="/admin")
