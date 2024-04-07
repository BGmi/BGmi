import asyncio
import sys
from typing import Any, Dict, List, Optional

import click
from loguru import logger
from nicegui import ui

from bgmi.config import cfg
from bgmi.lib import controllers as ctl
from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.fetch import website
from bgmi.lib.models import STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED, Bangumi, Filter, Followed, Subtitle
from bgmi.website.model import Episode

DEFAULT_BANGUMI_NAME = "Choose a Bangumi in Calander"


def async_wrapper(function: Any) -> Any:
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, function, *args, **kwargs)
        return result

    return wrapper


@ui.page("/")
async def main_page() -> None:
    with ui.header().classes(replace="row items-center"):
        with ui.tabs() as tabs:
            ui.tab("Calander").props("no-caps")
            ui.tab("Subscribe").props("no-caps")

    with ui.footer(value=False).style("background-color: #343741;").classes("items-center") as footer:
        ui.spinner(size="2em", color="blue")
        footer_label = ui.label("Submiting to download...")

    @async_wrapper
    def ctl_download(bangumi_list: List[str]) -> None:
        ctl.update(bangumi_list, download=True)

    def get_cur_bangumi() -> Optional[str]:
        cur_bangumi = None
        if panels.value == "Subscribe":
            cur_bangumi = bangumi_search_name.text
            if cur_bangumi == DEFAULT_BANGUMI_NAME:
                cur_bangumi = None
        return cur_bangumi

    async def do_download() -> None:
        cur_bangumi = get_cur_bangumi()

        bangumi_list = [cur_bangumi] if cur_bangumi else []

        if cur_bangumi:
            footer_label.set_text(f"Checking {cur_bangumi}...")
        else:
            footer_label.set_text("Checking all bangumi...")

        # footer_download_button.disable()
        footer.toggle()
        await ctl_download(bangumi_list)
        # footer_download_button.enable()
        footer.toggle()

    weekly_list = {}

    async def refresh_cur_page() -> None:
        cur_bangumi = get_cur_bangumi()
        if cur_bangumi:
            # Refresh bangumi info
            bangumi_detail_tab.refresh()
            ui.notify("Bangumi Info refreshed")
        else:
            # Force refresh weekly list
            nonlocal weekly_list
            weekly_list = await fetch_weekly_list(True)
            weekly_list_tab.refresh()
            ui.notify("Weekly list refreshed")

    with ui.tab_panels(tabs, value="Calander").classes("w-full") as panels:

        @async_wrapper
        def fetch_weekly_list(force_update: bool = False) -> Dict[str, List[Dict[str, Any]]]:
            return ctl.cal(cover=None, force_update=force_update, updating=only_show_updating_bgngumi_checkbox.value)

        loading_weekly_list = True

        def refresh_weekly_list_tab() -> None:
            nonlocal loading_weekly_list
            loading_weekly_list = True
            weekly_list_tab.refresh()

        @ui.refreshable
        async def weekly_list_tab() -> None:
            nonlocal loading_weekly_list
            nonlocal weekly_list

            if loading_weekly_list:
                ui.spinner(size="2em")
                weekly_list = await fetch_weekly_list(False)
                loading_weekly_list = False
                weekly_list_tab.refresh()
                return

            order_without_unknown = BANGUMI_UPDATE_TIME[:-1]
            weekday_order = order_without_unknown

            for weekday in weekday_order + ("Unknown",):
                weekday_bangumi = weekly_list.get(weekday.lower())
                if not weekday_bangumi:
                    continue
                ui.label(weekday).style("font-size: 150%;")

                def switch_to_subscribe(bangumi_name: str) -> None:
                    bangumi_search_name.set_text(bangumi_name)
                    panels.set_value("Subscribe")
                    bangumi_detail_tab.refresh()

                with ui.row().classes("items-center"):
                    for bangumi in sorted(weekday_bangumi, key=lambda x: int(x["id"])):
                        if bangumi["status"] in (STATUS_UPDATED, STATUS_FOLLOWED) and "episode" in bangumi:
                            bangumi_to_display = "{} ({:d})".format(bangumi["name"], bangumi["episode"])
                        else:
                            bangumi_to_display = bangumi["name"]

                        if bangumi["status"] in (STATUS_FOLLOWED, STATUS_UPDATED):
                            color = "green"
                        elif bangumi["status"] == STATUS_DELETED:
                            color = "blue"
                        else:
                            color = "grey"

                        ui.button(
                            bangumi_to_display,
                            on_click=lambda bangumi=bangumi: switch_to_subscribe(bangumi["name"]),
                            color=color,
                        ).props("no-caps")

        with ui.tab_panel("Calander"):

            async def refresh_weekly_list() -> None:
                nonlocal weekly_list
                weekly_list = await fetch_weekly_list(False)
                weekly_list_tab.refresh()

            with ui.row():
                ui.button(
                    "Refresh Weekly List",
                    on_click=refresh_cur_page,
                ).props("no-caps")
                ui.button(
                    "Download All Bangumi",
                    on_click=do_download,
                ).props("no-caps")
                only_show_updating_bgngumi_checkbox = ui.checkbox(
                    "Only show updating bangumi",
                    value=True,
                    on_change=refresh_weekly_list,
                )
            await weekly_list_tab()

        @ui.refreshable
        async def bangumi_detail_tab() -> None:
            bangumi_name = bangumi_search_name.text
            if bangumi_name == DEFAULT_BANGUMI_NAME:
                return

            with ui.row():
                ui.button(
                    "Refresh Bangumi Info",
                    on_click=refresh_cur_page,
                ).props("no-caps")
                ui.button(
                    "Download This Bangumi",
                    on_click=do_download,
                ).props("no-caps")

            followed = Followed.get_or_none(Followed.bangumi_name == bangumi_name)
            is_already_subscribed = followed is not None
            if is_already_subscribed:
                bangumi_instance = Bangumi.fuzzy_get(name=bangumi_name)

                bangumi_filter_obj = Filter.get_or_none(Filter.bangumi_name == bangumi_name)
                if bangumi_filter_obj:
                    filter_subtitle_group_ids = (bangumi_filter_obj.subtitle or "").split(", ")
                    filter_data = {
                        "include": bangumi_filter_obj.include,
                        "exclude": bangumi_filter_obj.exclude,
                        "regex": bangumi_filter_obj.regex,
                    }
                else:
                    filter_subtitle_group_ids = []
                    filter_data = {
                        "include": "",
                        "exclude": "",
                        "regex": "",
                    }

                loading_preview = True
                episode_preview = []

                @ui.refreshable
                async def preview_fetch() -> None:
                    nonlocal loading_preview
                    nonlocal episode_preview
                    if loading_preview:
                        ui.spinner(size="2em")
                        bangumi_obj = Bangumi.get(name=bangumi_name)

                        @async_wrapper
                        def fetch_episodes() -> List[Episode]:
                            _, data = website.get_maximum_episode(bangumi_obj, ignore_old_row=False)
                            return data

                        episode_preview = await fetch_episodes()
                        loading_preview = False
                        preview_fetch.refresh()
                    else:
                        with ui.column().style("gap: 0.0rem"):
                            for episode in episode_preview:
                                ui.label(episode.title)

                def refresh_preview() -> None:
                    nonlocal loading_preview
                    loading_preview = True
                    preview_fetch.refresh()

                with ui.splitter().classes("w-full").style("padding-top: 16px;") as splitter:
                    with splitter.before:
                        with ui.column().classes("w-full").style("padding-right: 16px; padding-bottom: 16px;"):
                            mark_episode_input = ui.number(label="Mark Episode", value=followed.episode, precision=0)

                            def input_forward(x: Optional[str]) -> str:
                                if x is None:
                                    return ""
                                return x

                            ui.input(label="Include", value=filter_data["include"]).bind_value(
                                filter_data, "include", forward=input_forward
                            ).classes("w-full")

                            ui.input(label="Exclude", value=filter_data["exclude"]).bind_value(
                                filter_data, "exclude", forward=input_forward
                            ).classes("w-full")

                            ui.input(label="Regex", value=filter_data["regex"]).bind_value(
                                filter_data, "regex", forward=input_forward
                            ).classes("w-full")

                            subtitle_groups = Subtitle.get_subtitle_by_id(bangumi_instance.subtitle_group.split(", "))

                            subtitle_select = ui.select(
                                [x["name"] for x in subtitle_groups],
                                multiple=True,
                                value=[x["name"] for x in subtitle_groups if x["id"] in filter_subtitle_group_ids],
                                label="Subtitle",
                            ).classes("w-full")

                            def on_save() -> None:
                                ctl.filter_(
                                    name=bangumi_name,
                                    subtitle=",".join(list(subtitle_select.value or [])),
                                    **filter_data,
                                )
                                try:
                                    episode = int(mark_episode_input.value)
                                except Exception:
                                    episode = 0
                                ctl.mark(bangumi_name, episode)
                                refresh_preview()
                                refresh_weekly_list_tab()

                            def show_delete_or_resubscribe() -> None:
                                async def on_delete() -> None:
                                    ctl.delete(
                                        name=bangumi_name,
                                    )
                                    bangumi_search_name.set_text(DEFAULT_BANGUMI_NAME)
                                    panels.set_value("Calander")
                                    refresh_weekly_list_tab()

                                async def on_resubscribe() -> None:
                                    ctl.add(
                                        name=bangumi_name,
                                        episode=followed.episode,
                                    )
                                    bangumi_detail_tab.refresh()
                                    refresh_weekly_list_tab()

                                try:
                                    is_deleted = Followed.get(bangumi_name=bangumi_name).status == STATUS_DELETED
                                except Exception:
                                    is_deleted = True

                                if is_deleted:
                                    ui.button("Resubscribe", on_click=on_resubscribe).props("no-caps")
                                else:
                                    ui.button("Delete", on_click=on_delete).props("no-caps")

                            with ui.row():
                                ui.button("Save", on_click=on_save).props("no-caps")
                                show_delete_or_resubscribe()

                    with splitter.after:
                        with ui.column().style("padding-left: 16px"):
                            ui.label("Preview").style("font-size: 150%;")
                            await preview_fetch()
            else:

                async def do_subscribe() -> None:
                    try:
                        episode = int(subscribe_episode_input.value)
                    except Exception:
                        episode = 0
                    ui.spinner(size="lg")

                    @async_wrapper
                    def add_wrapper() -> None:
                        ctl.add(bangumi_name, episode)

                    await add_wrapper()

                    bangumi_detail_tab.refresh()
                    weekly_list_tab.refresh()

                with ui.row().style("align-items: center;"):
                    subscribe_episode_input = ui.number(label="Episode", value=0, precision=0)
                    ui.button("Subscribe", color="green").on_click(do_subscribe).props("no-caps")

        with ui.tab_panel("Subscribe"):
            bangumi_search_name = ui.label(DEFAULT_BANGUMI_NAME).style("font-size: 200%;")

            await bangumi_detail_tab()


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=8080, type=int)
def main(host, port):
    logger.remove()
    logger.add(
        sys.stderr, format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> {level:7} | <level>{message}</level>", level="INFO"
    )
    logger.add(cfg.log_path.parent.joinpath("{time:YYYY-MM-DD}.log"), format="{time} {level} {message}", level="INFO")

    ui.run(host=host, port=port, title="BGmi")


if __name__ in {"__main__", "__mp_main__"}:
    main()
