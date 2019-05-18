import datetime
import imghdr
import itertools
import os
import re
import string
import sys
from functools import wraps

import click
import peewee

import bgmi.setup
import bgmi.website
from bgmi import config
from bgmi.lib import constants, controllers
from bgmi.lib.constants import DOWNLOAD_CHOICE_LIST_DICT, SPACIAL_APPEND_CHARS, SPACIAL_REMOVE_CHARS
from bgmi.lib.constants.actions import ACTIONS
from bgmi.lib.download import download_prepare, get_download_class
from bgmi.lib.fetch import website
from bgmi.lib.models import Bangumi, Followed, get_kv_storage
from bgmi.lib.update import upgrade_version
from bgmi.script import ScriptRunner
from bgmi.sql import init_db
from bgmi.utils import (
    COLOR_END, GREEN, RED, YELLOW, check_update, convert_cover_url_to_path, download_cover,
    get_terminal_col, get_web_admin, print_error, print_info, print_success, print_warning,
    render_template
)


def action_decorator(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapped


class GroupWithCommandOptions(click.Group):
    """ Allow application of options to group with multi command """

    def add_command(self, cmd, name=None):
        """ Hook the added command and put the group options on the command """
        click.Group.add_command(self, cmd, name=name)

        # add the group parameters to the command
        for param in self.params:
            cmd.params.append(param)

        # hook the command's invoke with our own
        cmd.invoke = self.build_command_invoke(cmd.invoke)
        self.invoke_without_command = True

    def build_command_invoke(self, original_invoke):
        def command_invoke(ctx):
            """ insert invocation of group function """

            # separate the group parameters
            ctx.obj = dict(_params=dict())
            for param in self.params:
                name = param.name
                ctx.obj['_params'][name] = ctx.params[name]
                del ctx.params[name]

            # call the group function with its parameters
            params = ctx.params
            ctx.params = ctx.obj['_params']
            self.invoke(ctx)
            ctx.params = params

            # now call (invoke) the original command
            original_invoke(ctx)

        return command_invoke


@click.group()
def meta_cli():
    print('meta command')


@meta_cli.command(help='Install BGmi front / download delegate and initialize database')
@click.option(
    '--no-web',
    default=False,
    show_default=True,
    type=bool,
    flag_value=True,
    help='Don\'t download web static file.'
)
def install(no_web: bool = False):
    """
    install bangumi on your local
    """
    if not os.path.exists(config.BGMI_PATH):
        print_warning('BGMI_PATH %s does not exist, installing' % config.BGMI_PATH)

    bgmi.setup.create_dir()
    bgmi.setup.install_crontab()
    init_db()

    if constants.kv.OLD_VERSION not in get_kv_storage():
        get_kv_storage()[constants.kv.OLD_VERSION] = bgmi.__version__
    if not no_web:
        get_web_admin()
    else:
        print_info('skip downloading web static files')


@meta_cli.command(help='Migrate from old version.')
def upgrade():
    bgmi.setup.create_dir()
    upgrade_version()
    check_update(mark=False)


@click.group(cls=GroupWithCommandOptions)
def normal_cli():
    try:
        check_update()
    except peewee.OperationalError:
        if os.getenv('DEBUG'):
            raise
        print_error('call `bgmi install` to install bgmi')


@normal_cli.command('config', help='Config BGmi')
@click.argument('name', required=False)
@click.argument('value', required=False)
def config_wrapper(name=None, value=None):
    if name == 'DB_URL':
        if value:
            from playhouse.db_url import schemes

            scheme = value.split('://')[0]
            if scheme not in schemes:
                print_error(
                    '{} if not a supported schemes, only support "`{}`"'.format(
                        scheme, '`, `'.join(schemes.keys())
                    )
                )
                return

    result = controllers.config_(name, value)
    result.print(indicator=False)
    if name == 'DB_URL' and value:
        print_info('you are editing DB_URL, please run `bgmi install` to init db')


@normal_cli.command('search', help='Search torrents from data source by keyword')
@click.argument('keyword')
@click.option(
    '--count',
    type=int,
    default=int(config.MAX_PAGE),
    show_default=True,
    help='The max page count of search result.'
)
@click.option(
    '--regex-filter', type=str, show_default=True, help='Regular expression filter of title.'
)
@click.option(
    '--dupe', type=bool, flag_value=True, show_default=True, help='Download search result.'
)
@click.option('--min-episode', type=int, show_default=True, help='Minimum episode filter of title.')
@click.option('--max-episode', type=int, show_default=True, help='Maximum episode filter of title.')
@click.option(
    '--download', type=bool, show_default=True, flag_value=True, help='Show duplicated episode'
)
def search_wrapper(
    keyword: str,
    count: int,
    regex_filter: str = None,
    dupe: bool = False,
    min_episode: int = None,
    max_episode: int = None,
    download: bool = False,
):
    result = controllers.search(
        keyword=keyword,
        count=count,
        regex=regex_filter,
        dupe=dupe,
        min_episode=min_episode,
        max_episode=max_episode
    )
    if result['status'] != 'success':
        globals()['print_{}'.format(result['status'])](result['message'])
    data = result['data']
    for i in data:
        print_success(i['title'])
    if download:
        download_prepare(data)


@normal_cli.command(help='Mark bangumi episode.')
@click.argument('bangumi_name', type=str)
@click.argument('episode', type=int)
def mark(bangumi_name, episode):
    result = controllers.mark(name=bangumi_name, episode=episode)
    globals()['print_{}'.format(result['status'])](result['message'])


def delete(ret):
    if ret.clear_all:
        controllers.delete_('', clear_all=ret.clear_all, batch=ret.batch)
    else:
        for bangumi_name in ret.name:
            result = controllers.delete_(name=bangumi_name)
            globals()['print_{}'.format(result['status'])](result['message'])


@normal_cli.command()
@click.argument('names', nargs=-1)
@click.option('--episode', type=int, help='mark bangumi as specified episode.')
def add(names, episode=None):
    """
    Subscribe bangumi or baugumis
    """
    for bangumi_name in names:
        result = controllers.add(name=bangumi_name, episode=episode)
        globals()['print_{}'.format(result['status'])](result['message'])


@normal_cli.command('list', help='List subscribed bangumi.')
def list_wrapper():
    result = controllers.list_()
    print(result['message'])


def cover_has_downloaded(url: str) -> bool:
    """
    check is a cover url exists on disk and if its a valid image file
    Args:
        url: cover image url

    Returns:

    """
    _, file_path = convert_cover_url_to_path(url)
    return os.path.exists(file_path) and imghdr.what(file_path)


@click.command('cal')
@click.option('--force-update', '-f', help='force update when showing calendar')
@click.option('--no-save', help='not save to db')
@click.option('--download-cover', help='download cover')
def cal_wrapper(ret):
    save = not ret.no_save
    runner = ScriptRunner()

    weekly_list = website.bangumi_calendar(force_update=ret.force_update, save=save)
    patch_list = runner.get_models_dict()
    for i in patch_list:
        weekly_list[i['update_time'].lower()].append(i)

    # download cover to local
    if ret.download_cover:
        cover_to_be_download = [
            x for x in runner.get_download_cover() if not cover_has_downloaded(x)
        ]

        for daily_bangumi in weekly_list.values():
            for bangumi in daily_bangumi:
                if not cover_has_downloaded(bangumi['cover']):
                    cover_to_be_download.append(bangumi['cover'])

        if cover_to_be_download:
            print_info('Updating cover ...')
            download_cover(cover_to_be_download)

    def shift(seq, n):
        n %= len(seq)
        return seq[n:] + seq[:n]

    if ret.today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()], )
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    if os.environ.get('TRAVIS_CI', False):
        env_columns = 42
    else:
        env_columns = get_terminal_col()

    col = 42

    if env_columns < col:
        print_warning('terminal window is too small.')
        env_columns = col

    row = int(env_columns / col if env_columns / col <= 3 else 3)

    def print_line():
        num = col - 3
        split = '-' * num + '   '
        print(split * row)

    for weekday in weekday_order:
        if weekly_list[weekday.lower()]:
            print(
                '{}{}. {}'.format(
                    GREEN,
                    weekday if not ret.today else 'Bangumi Schedule for Today (%s)' % weekday,
                    COLOR_END
                )
            )
            print_line()
            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if bangumi['status'] in (
                    Followed.STATUS.UPDATED,
                    Followed.STATUS.FOLLOWED,
                ) and 'episode' in bangumi:
                    bangumi['name'] = '%s(%d)' % (bangumi['name'], bangumi['episode'])

                half = len(re.findall('[%s]' % string.printable, bangumi['name']))
                full = (len(bangumi['name']) - half)
                # print(full, " ", half, "'", bangumi['name'], "'", sep='', end=' ')

                space_count = col - 2 - (full * 2 + half)

                for s in SPACIAL_APPEND_CHARS:
                    if s in bangumi['name']:
                        space_count += bangumi['name'].count(s)

                for s in SPACIAL_REMOVE_CHARS:
                    if s in bangumi['name']:
                        space_count -= bangumi['name'].count(s)

                if bangumi['status'] == Followed.STATUS.FOLLOWED:
                    bangumi['name'] = '{}{}{}'.format(YELLOW, bangumi['name'], COLOR_END)

                if bangumi['status'] == Followed.STATUS.UPDATED:
                    bangumi['name'] = '{}{}{}'.format(GREEN, bangumi['name'], COLOR_END)
                print(' ' + bangumi['name'], ' ' * space_count, end='')

                if (i + 1) % row == 0 or i + 1 == len(weekly_list[weekday.lower()]):
                    print()
            print()


def filter_wrapper(ret):
    result = controllers.filter_(
        name=ret.name,
        data_source_input=ret.data_source,
        subtitle_input=ret.subtitle,
        include=ret.include,
        exclude=ret.exclude,
        regex=ret.regex
    )
    result.print()
    if result.data:
        print_info('Usable subtitle group: {}'.format(result.data['subtitle_group']))
        print_info('Usable data source: {}'.format(result.data['data_source']))
        print()
        followed_filter_obj = result.data['obj']
        print_filter(followed_filter_obj)
    return result.data


def update_wrapper(ret):
    controllers.update(name=ret.name, download=ret.download, not_ignore=ret.not_ignore)


def download_manager(ret):
    if ret.id:
        # 没有入口..
        download_id = ret.id
        status = ret.status
        if download_id is None or status is None:
            print_error('No id or status specified.')
        # download_obj = NeoDownload.get(_id=download_id)
        # if not download_obj:
        #     print_error('Download object does not exist.')
        # print_info(
        #     'Download Object <{0} - {1}>, Status: {2}'.format(
        #         download_obj.name,
        #         download_obj.episode,
        #         download_obj.status,
        #     )
        # )
        # download_obj.status = status
        # download_obj.save()
        print_success(
            'Download status has been marked as {}'.format(
                DOWNLOAD_CHOICE_LIST_DICT.get(int(status))
            )
        )
    else:
        status = ret.status
        status = int(status) if status is not None else None
        delegate = get_download_class()
        delegate.download_status(status=status)


def fetch_(ret):
    try:
        bangumi_obj = Bangumi.get(name=ret.name)
        Followed.get(bangumi_id=bangumi_obj.id)
    except Bangumi.DoesNotExist:
        print_error('Bangumi {} not exist'.format(ret.name))
        return
    except Followed.DoesNotExist:
        print_error('Bangumi {} is not followed'.format(ret.name))
        return

    followed_filter_obj = Followed.get(bangumi_id=bangumi_obj.id)
    print_filter(followed_filter_obj)

    print_info('Fetch bangumi {} ...'.format(bangumi_obj.name))
    # False if ret.not_ignore else True
    _, data = website.get_maximum_episode(bangumi_obj, ignore_old_row=not ret.not_ignore)

    if not data:
        print_warning('Nothing.')
    for i in data:
        print_success(i['title'])


@normal_cli.command(help='List your history of following bangumi')
def history():
    m = (
        'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
        'October', 'November', 'December'
    )
    data = Followed.select(Followed).order_by(Followed.updated_time.asc())
    bangumi_data = Bangumi.get_updating_bangumi()
    year = None
    month = None

    updating_bangumi = list(map(lambda s: s['name'], itertools.chain(*bangumi_data.values())))

    print_info('Bangumi Timeline')
    for i in data:
        if i.status == Followed.STATUS.DELETED:
            slogan = 'ABANDON'
            color = RED
        else:
            if i.bangumi_name in updating_bangumi:
                slogan = 'FOLLOWING'
                color = YELLOW
            else:
                slogan = 'FINISHED'
                color = GREEN

        if not i.updated_time:
            # can't be 0, will raise OSError on windows
            date = datetime.datetime.fromtimestamp(100000)
        else:
            date = datetime.datetime.fromtimestamp(int(i.updated_time))

        if date.year != 1970:
            if date.year != year:
                print('{}{}{}'.format(GREEN, str(date.year), COLOR_END))
                year = date.year

            if date.year == year and date.month != month:
                print('  |\n  |--- {}{}{}\n  |      |'.format(YELLOW, m[date.month - 1], COLOR_END))
                month = date.month

            print(
                '  |      |--- [%s%-9s%s] (%-2s) %s' %
                (color, slogan, COLOR_END, i.episode, i.bangumi_name)
            )


def config_gen(ret):
    template_file_path = os.path.join(os.path.dirname(__file__), '..', 'others', ret.config)

    if ret.config == 'nginx.conf':
        no_server_name = False
        if not ret.server_name:
            no_server_name = True
            ret.server_name = '_'

        template_with_content = render_template(
            template_file_path,
            actions=ACTIONS,
            server_name=ret.server_name,
            os_sep=os.sep,
            front_static_path=config.FRONT_STATIC_PATH,
            save_path=config.SAVE_PATH
        )
        print(template_with_content)
        if no_server_name:
            print('# not giving a server name, take `_` as default server name')
            print('# usage: `bgmi gen nginx.conf --server-name bgmi.my-website.com`')
    elif ret.config == 'bgmi_http.service':
        user = os.environ.get('USER', os.environ.get('USERNAME'))
        template_with_content = render_template(
            template_file_path, python_path=sys.executable, user=user
        )
        print(template_with_content)
    elif ret.config == 'caddyfile':
        if not ret.server_name:
            ret.server_name = 'localhost'

        template_with_content = render_template(
            template_file_path,
            server_name=ret.server_name,
            front_static_path=config.FRONT_STATIC_PATH,
            save_path=config.SAVE_PATH
        )
        print(template_with_content)


@normal_cli.command(
    help='Run bgmi front server',
    context_settings={
        'ignore_unknown_options': True,
        'allow_extra_args': True,
    },
)
def serve():
    from bgmi.front.server import main
    main()


def print_filter(followed_filter_obj: Followed):
    def j(x):
        return x or 'None'

    print_info('Followed subtitle group: {}'.format(j(followed_filter_obj.subtitle)))
    print_info('Followed data sources: {}'.format(j(followed_filter_obj.data_source)))
    print_info('Include keywords: {}'.format(j(followed_filter_obj.include)))
    print_info('Exclude keywords: {}'.format(j(followed_filter_obj.exclude)))
    print_info('Regular expression: {}'.format(j(followed_filter_obj.regex)))
    print_info('(`None` means noneffective filter)')


cli = click.CommandCollection(sources=[meta_cli, normal_cli], invoke_without_command=True)
