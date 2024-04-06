from nicegui import ui
from bgmi.lib import controllers as ctl

from bgmi.lib.constants import BANGUMI_UPDATE_TIME
from bgmi.lib.fetch import website
import subprocess
from bgmi.lib.models import STATUS_DELETED, STATUS_FOLLOWED, STATUS_UPDATED, Bangumi, Filter, Followed, Subtitle
import time
import asyncio

import argparse


DEFAULT_BANGUMI_NAME = 'Choose a Bangumi in Calander'


def async_wrapper(function):
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, function, *args, **kwargs)
        return result
    return wrapper


@ui.page('/')
async def main_page():
    with ui.header().classes(replace='row items-center'):
        with ui.tabs() as tabs:
            ui.tab('Calander')
            ui.tab('Subscribe')

    with ui.footer(value=False).style('background-color: #343741;').classes('items-center') as footer:
        ui.spinner(size='2em', color='blue')
        ui.label('Downloading...')

    with ui.tab_panels(tabs, value='Calander').classes('w-full') as panels:
        @ui.refreshable
        async def weekly_list_tab():
            @async_wrapper
            def fetch_weekly_list():
                return ctl.cal(cover=None)
            weekly_list = await fetch_weekly_list()

            @async_wrapper
            def ctl_download():
                ctl.update([], download=True)
                time.sleep(5)
                subprocess.run([
                    '/home/elsa/miniconda3/bin/python',
                    '/mnt/cloud/Code/animate/bgmi-renamer.py'
                ])

            async def do_download():
                footer_button.disable()
                footer.toggle()
                await ctl_download()
                footer_button.enable()
                footer.toggle()

            with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
                footer_button = ui.button(on_click=do_download,
                                          icon='download').props('fab')
            order_without_unknown = BANGUMI_UPDATE_TIME[:-1]
            weekday_order = order_without_unknown

            for weekday in weekday_order + ("Unknown",):
                weekday_bangumi = weekly_list.get(weekday.lower())
                if not weekday_bangumi:
                    continue
                ui.label(weekday).style('font-size: 150%;')

                def switch_to_subscribe(bangumi_name):
                    bangumi_search_name.set_text(bangumi_name)
                    panels.set_value('Subscribe')
                    subscribe_bangumi.refresh()

                with ui.row().classes('items-center'):
                    for bangumi in weekday_bangumi:
                        if bangumi["status"] in (STATUS_UPDATED, STATUS_FOLLOWED) and "episode" in bangumi:
                            bangumi_to_display = "{} ({:d})".format(
                                bangumi["name"], bangumi["episode"])
                        else:
                            bangumi_to_display = bangumi["name"]

                        if bangumi["status"] in (STATUS_FOLLOWED, STATUS_UPDATED):
                            color = 'green'
                        elif bangumi["status"] == STATUS_DELETED:
                            color = 'blue'
                        else:
                            color = 'grey'

                        ui.button(
                            bangumi_to_display,
                            on_click=lambda bangumi=bangumi: switch_to_subscribe(
                                bangumi['name']),
                            color=color,
                        )
        with ui.tab_panel('Calander'):
            await weekly_list_tab()

        @ui.refreshable
        async def subscribe_bangumi():
            bangumi_name = bangumi_search_name.text
            if bangumi_name == DEFAULT_BANGUMI_NAME:
                return

            is_already_subscribed = Followed.get_or_none(
                Followed.bangumi_name == bangumi_name) is not None
            if is_already_subscribed:
                bangumi_instance = Bangumi.fuzzy_get(name=bangumi_name)

                bangumi_filter_obj = Filter.get_or_none(
                    Filter.bangumi_name == bangumi_name)
                if bangumi_filter_obj:
                    filter_subtitle_group_ids = (bangumi_filter_obj.subtitle or '').split(
                        ',')
                    filter_data = {
                        'include': bangumi_filter_obj.include,
                        'exclude': bangumi_filter_obj.exclude,
                        'regex': bangumi_filter_obj.regex,
                    }
                else:
                    filter_subtitle_group_ids = []
                    filter_data = {
                        'include': '',
                        'exclude': '',
                        'regex': '',
                    }

                loading_preview = True
                episode_preview = []

                @ui.refreshable
                async def preview_fetch():
                    nonlocal loading_preview
                    if loading_preview:
                        ui.spinner(size='2em')
                        bangumi_obj = Bangumi.get(name=bangumi_name)

                        @async_wrapper
                        def fetch_episodes():
                            _, data = website.get_maximum_episode(
                                bangumi_obj, ignore_old_row=False)
                            return data
                        nonlocal episode_preview
                        episode_preview = await fetch_episodes()
                        loading_preview = False
                        preview_fetch.refresh()
                    else:
                        with ui.column().style('gap: 0.0rem'):
                            for episode in episode_preview:
                                ui.label(episode.title)

                def refresh_preview():
                    nonlocal loading_preview
                    loading_preview = True
                    preview_fetch.refresh()

                with ui.splitter().classes('w-full') as splitter:
                    with splitter.before:
                        with ui.column().style('padding: 10px'):
                            ui.label('Filter').style('font-size: 150%;')

                            def input_forward(x):
                                if x is None:
                                    return ''
                                return x

                            ui.input(label='Include', value=filter_data['include']).bind_value(
                                filter_data, 'include', forward=input_forward)

                            ui.input(label='Exclude', value=filter_data['exclude']).bind_value(
                                filter_data, 'exclude', forward=input_forward)

                            ui.input(label='Regex', value=filter_data['regex']).bind_value(
                                filter_data, 'regex', forward=input_forward)

                            ui.label('Subtitle').style('font-size: 150%;')
                            subtitle_groups = Subtitle.get_subtitle_by_id(
                                bangumi_instance.subtitle_group.split(", "))
                            selected_subtitle = set()

                            def on_change_checkbox(event, subtitle_name):
                                if event.value:
                                    selected_subtitle.add(subtitle_name)
                                else:
                                    selected_subtitle.remove(subtitle_name)

                            with ui.column().style('gap: 0.1rem'):
                                for x in subtitle_groups:
                                    with ui.row().classes('items-center'):
                                        selected = x['id'] in filter_subtitle_group_ids

                                        ui.checkbox(
                                            value=selected,
                                            on_change=lambda value, x=x: on_change_checkbox(
                                                value, x['name'])
                                        )
                                        ui.label(text=x['name']).classes(
                                            'flex-grow')
                                        if selected:
                                            selected_subtitle.add(x['name'])

                            def on_save():
                                ctl.filter_(
                                    name=bangumi_name,
                                    subtitle=','.join(selected_subtitle),
                                    **filter_data,
                                )
                                refresh_preview()

                            async def on_delete():
                                ctl.delete(
                                    name=bangumi_name,
                                )
                                bangumi_search_name.set_text(
                                    DEFAULT_BANGUMI_NAME)
                                panels.set_value('Calander')
                                weekly_list_tab.refresh()

                            with ui.row():
                                ui.button('Save', on_click=on_save)
                                ui.button('Delete', on_click=on_delete)
                    with splitter.after:
                        with ui.column().style('padding: 10px'):
                            ui.label('Preview').style('font-size: 150%;')
                            await preview_fetch()
            else:
                async def do_subscribe():
                    try:
                        episode = int(episode_input.value)
                    except Exception:
                        episode = 0
                    ui.spinner(size='lg')

                    @async_wrapper
                    def add_wrapper():
                        ctl.add(bangumi_name, episode)
                    await add_wrapper()

                    subscribe_bangumi.refresh()
                    weekly_list_tab.refresh()

                with ui.row().style('align-items: center;'):
                    episode_input = ui.number(
                        label='Episode', value=0, precision=0)
                    ui.button('Subscribe', color='green').on_click(
                        do_subscribe)

        with ui.tab_panel('Subscribe'):
            bangumi_search_name = ui.label(
                DEFAULT_BANGUMI_NAME).style('font-size: 200%;')

            await subscribe_bangumi()

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost')
parser.add_argument('--port', default=8080, type=int)

args = parser.parse_args()

ui.run(host=args.host, port=args.port)
