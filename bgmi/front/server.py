import asyncio

import click
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from bgmi.config import IS_WINDOWS, cfg
from bgmi.front.resources import CalendarHandler
from .routes import app as api


@click.command()
@click.option(
    "--port",
    type=int,
    default=8888,
    help="listen on the port",
)
@click.option("--address", default="0.0.0.0", help="binding at given address", type=str)
def main(address: str, port: int) -> None:
    if IS_WINDOWS:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    app = make_app()

    print(f"BGmi HTTP Server listening on {address}:{port:d}")
    uvicorn.run(app, host=address, port=port)


def index_need_config(_: Request) -> HTMLResponse:
    return HTMLResponse(
        "<h1>BGmi HTTP Service</h1>"
        "<pre>Please modify your web server configure file\n"
        f"to server this path to '{cfg.save_path}'.\n"
        "e.g.\n\n"
        "...\n"
        "autoindex on;\n"
        "location / {\n"
        f"    alias {cfg.front_static_path.as_posix()}/;\n"
        "}\n"
        "location /bangumi {\n"
        f"    alias {cfg.save_path.as_posix()}/;\n"
        "}\n"
        "...\n\n"
        "If use want main to serve static files, please run this command and <strong>restart main</strong>\n"
        "\n"
        "<code>bgmi config set http serve_static_files --value true</code></pre>"
    )


def make_app() -> Starlette:
    routes = [
        Mount("/api/", app=api),
        Route("/resource/calendar.ics", CalendarHandler),
    ]

    if cfg.http.serve_static_files:
        print("will handle static files")
        routes.extend(
            [
                Mount("/bangumi", app=StaticFiles(directory=cfg.save_path)),
                Mount("/", app=StaticFiles(directory=cfg.front_static_path, html=True)),
            ]
        )
    else:
        routes.extend(
            [
                Route("/bangumi/", endpoint=index_need_config),
                Route("/", endpoint=index_need_config),
            ]
        )

    app = Starlette(routes=routes)

    return app


if __name__ == "__main__":
    main(address="127.0.0.1", port=8999)
