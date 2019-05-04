import datetime
import imghdr
import itertools
import os
import re
import string
import sys
from functools import wraps

import bgmi.config
import bgmi.website
from bgmi.lib.constants import (
    ACTION_ADD, ACTION_CAL, ACTION_CONFIG, ACTION_CONFIG_GEN, ACTION_DELETE, ACTION_DOWNLOAD,
    ACTION_FETCH, ACTION_FILTER, ACTION_LIST, ACTION_MARK, ACTION_SEARCH, ACTION_UPDATE,
    DOWNLOAD_CHOICE_LIST_DICT, SPACIAL_APPEND_CHARS, SPACIAL_REMOVE_CHARS, SUPPORT_WEBSITE,
    actions_and_arguments
)
from bgmi.lib.constants.actions import ACTION_COMPLETE, ACTION_HISTORY, ACTIONS
from bgmi.lib.controllers import add, config_, delete, filter_, list_, mark, search, update
from bgmi.lib.download import download_prepare, get_download_class
from bgmi.lib.fetch import website
from bgmi.lib.models import Bangumi, Followed
from bgmi.logger import logger
from bgmi.script import ScriptRunner
from bgmi.utils import (
    COLOR_END, GREEN, RED, YELLOW, convert_cover_url_to_path, download_cover, get_terminal_col,
    print_error, print_info, print_success, print_warning, render_template
)


def action_decorator(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapped


def config_wrapper(ret):
    name = ret.name
    value = ret.value
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

    result = config_(ret.name, ret.value)
    result.print()
    # if (not ret.name) and (not ret.value):
    #     print(result['message'])
    # else:
    if ret.name == 'DB_URL' and ret.value:
        print_info('you are editing DB_URL, please run `bgmi install` to init db')

        # globals()["print_{}".format(result['status'])](result['message'])


def search_wrapper(ret):
    result = search(
        keyword=ret.keyword,
        count=ret.count,
        regex=ret.regex_filter,
        dupe=ret.dupe,
        min_episode=ret.min_episode,
        max_episode=ret.max_episode
    )
    if result['status'] != 'success':
        globals()['print_{}'.format(result['status'])](result['message'])
    data = result['data']
    for i in data:
        print_success(i['title'])
    if ret.download:
        download_prepare(data)


def mark_wrapper(ret):
    result = mark(name=ret.name, episode=ret.episode)
    globals()['print_{}'.format(result['status'])](result['message'])


def delete_wrapper(ret):
    if ret.clear_all:
        delete('', clear_all=ret.clear_all, batch=ret.batch)
    else:
        for bangumi_name in ret.name:
            result = delete(name=bangumi_name)
            globals()['print_{}'.format(result['status'])](result['message'])


def add_wrapper(ret):
    for bangumi_name in ret.name:
        result = add(name=bangumi_name, episode=ret.episode)
        globals()['print_{}'.format(result['status'])](result['message'])


def list_wrapper(ret):
    result = list_()
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


def cal_wrapper(ret):
    save = not ret.no_save
    runner = ScriptRunner()

    weekly_list = website.bangumi_calendar(force_update=ret.force_update, save=save)
    # if os.environ.get('DEBUG') or ret.show_source:
    #     pass
    # todo
    # for bangumi_list in weekly_list.values():
    #     for bangumi in bangumi_list:
    #         bangumi['name'] = bangumi['name'] + ' {' + '{}'.format(
    #             ', '.join([x[:min(1, len(x))] for x in bangumi['data_source'].keys()]) + '}'
    #         )
    #
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
    result = filter_(
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
    update(name=ret.name, download=ret.download, not_ignore=ret.not_ignore)


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
        delegate = get_download_class(instance=False)
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


def complete(ret):
    # coding=utf-8
    """`eval "$(bgmi complete)"` to complete bgmi in bash"""
    updating_bangumi_names = [x['name'] for x in Bangumi.get_updating_bangumi(order=False)]

    all_config = bgmi.config.__writeable__

    actions_and_opts = {}
    helper = {}
    for action_dict in actions_and_arguments:
        actions_and_opts[action_dict['action']] = []
        for arg in action_dict.get('arguments', []):
            if isinstance(arg['dest'], str) and arg['dest'].startswith('-'):
                actions_and_opts[action_dict['action']].append(arg)
            elif isinstance(arg['dest'], list):
                actions_and_opts[action_dict['action']].append(arg)
        helper[action_dict['action']] = action_dict.get('help', '')

    if 'bash' in os.getenv('SHELL').lower():  # bash
        template_file_path = os.path.join(
            os.path.dirname(__file__), '..', 'others', '_bgmi_completion_bash.sh'
        )

    elif 'zsh' in os.getenv('SHELL').lower():  # zsh
        template_file_path = os.path.join(
            os.path.dirname(__file__), '..', 'others', '_bgmi_completion_zsh.sh'
        )

    else:
        print('unsupported shell {}'.format(os.getenv('SHELL').lower()), file=sys.stderr)
        return

    template_with_content = render_template(
        template_file_path,
        ctx=dict(
            actions=ACTIONS,
            bangumi=updating_bangumi_names,
            config=all_config,
            actions_and_opts=actions_and_opts,
            source=[x['id'] for x in SUPPORT_WEBSITE],
            helper=helper,
            isinstance=isinstance,
            string_types=str
        )
    )
    if os.environ.get('DEBUG', False):  # pragma: no cover
        with open('./_bgmi', 'w+', encoding='utf8') as template_file:
            template_file.write(template_with_content)
    print(template_with_content)


def history(ret):
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
            front_static_path=bgmi.config.FRONT_STATIC_PATH,
            save_path=bgmi.config.SAVE_PATH
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
            front_static_path=bgmi.config.FRONT_STATIC_PATH,
            save_path=bgmi.config.SAVE_PATH
        )
        print(template_with_content)


CONTROLLERS_DICT = {
    ACTION_ADD: add_wrapper,
    ACTION_CAL: cal_wrapper,
    ACTION_CONFIG: config_wrapper,
    ACTION_CONFIG_GEN: config_gen,
    ACTION_COMPLETE: complete,
    ACTION_DOWNLOAD: download_manager,
    ACTION_DELETE: delete_wrapper,
    ACTION_FETCH: fetch_,
    ACTION_FILTER: filter_wrapper,
    ACTION_HISTORY: history,
    ACTION_LIST: list_wrapper,
    ACTION_MARK: mark_wrapper,
    ACTION_SEARCH: search_wrapper,
    ACTION_UPDATE: update_wrapper,
}


def controllers(ret):
    logger.info(ret)
    func = CONTROLLERS_DICT.get(ret.action, None)
    if not callable(func):
        return
    return func(ret)


def print_filter(followed_filter_obj: Followed):
    def j(x):
        if x:
            return ', '.join(x)
        return 'None'

    print_info('Followed subtitle group: {}'.format(j(followed_filter_obj.subtitle)))
    print_info('Followed data sources: {}'.format(j(followed_filter_obj.data_source)))
    print_info('Include keywords: {}'.format(j(followed_filter_obj.include)))
    print_info('Exclude keywords: {}'.format(j(followed_filter_obj.exclude)))
    print_info('Regular expression: {}'.format(followed_filter_obj.regex))
    print_info('(`None` means noneffective filter)')
