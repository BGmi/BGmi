import bgmi.config

from . import kv, namespace
from .actions import (
    ACTION_ADD, ACTION_CAL, ACTION_COMPLETE, ACTION_CONFIG, ACTION_CONFIG_GEN, ACTION_DELETE,
    ACTION_DOWNLOAD, ACTION_FETCH, ACTION_FILTER, ACTION_LIST, ACTION_MARK, ACTION_SEARCH,
    ACTION_UPDATE
)

SECOND_OF_WEEK = 7 * 24 * 3600

DOWNLOAD_ACTION_LIST = 'list'
DOWNLOAD_ACTION_MARK = 'mark'
DOWNLOAD_ACTION = (DOWNLOAD_ACTION_LIST, DOWNLOAD_ACTION_MARK)

DOWNLOAD_CHOICE_LIST_ALL = 'all'
DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD = 'not_downloaded'
DOWNLOAD_CHOICE_LIST_DOWNLOADING = 'downloading'
DOWNLOAD_CHOICE_LIST_DOWNLOADED = 'downloaded'
DOWNLOAD_CHOICE_LIST_DICT = {
    None: DOWNLOAD_CHOICE_LIST_ALL,
    0: DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD,
    1: DOWNLOAD_CHOICE_LIST_DOWNLOADING,
    2: DOWNLOAD_CHOICE_LIST_DOWNLOADED,
}

DOWNLOAD_CHOICE = (
    DOWNLOAD_CHOICE_LIST_ALL, DOWNLOAD_CHOICE_LIST_DOWNLOADED, DOWNLOAD_CHOICE_LIST_DOWNLOADING,
    DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD
)

FOLLOWED_ACTION_LIST = 'list'
FOLLOWED_ACTION_MARK = 'mark'
FOLLOWED_CHOICE = (FOLLOWED_ACTION_LIST, FOLLOWED_ACTION_MARK)
SUPPORT_WEBSITE = [
    {
        'view': '萌番组 https://bangumi.moe/',
        'id': 'bangumi_moe',
    },
    {
        'view': '蜜柑计划 https://mikanani.me/',
        'id': 'mikan_project',
    },
    {
        'view': '动漫花园 http://share.dmhy.org/',
        'id': 'dmhy',
    },
]
STATUS_SUCCESS = 'success'
STATUS_WARNING = 'warning'
STATUS_ERROR = 'error'
STATUS_INFO = 'info'

SPACIAL_APPEND_CHARS = 'ⅡⅢⅥ♪Δ×☆É·♭★‧☆'
SPACIAL_REMOVE_CHARS = ''

UNSUPPORTED_VIDEO_CODING = [
    'hevc',
]
COMMON_EXCLUDE_KEYWORD = UNSUPPORTED_VIDEO_CODING

# There should be no `'` in any help message
actions_and_arguments = [
    {
        'action': ACTION_ADD,
        'help': 'Subscribe bangumi.',
        'arguments': [
            {
                'dest': 'name',
                'kwargs': dict(metavar='name', nargs='+', help='Bangumi name'),
            },
            {
                'dest': '--episode',
                'kwargs': dict(
                    metavar='episode',
                    help='Add bangumi and mark it as specified episode.',
                    type=int,
                ),
            },
            {
                'dest': '--not-ignore',
                'kwargs': dict(
                    action='store_true',
                    help='Do not ignore the old bangumi detail rows (3 month ago).',
                ),
            },
        ],
    },
    {
        'action': ACTION_DELETE,
        'help': 'Unsubscribe bangumi.',
        'arguments': [
            {
                'dest': '--name',
                'kwargs': dict(metavar='name', nargs='+', help='Bangumi name to unsubscribe.'),
            },
            {
                'dest': '--clear-all',
                'kwargs': dict(
                    action='store_true',
                    help='Clear all the subscriptions,'
                    ' name will be ignored If you provide this flag.'
                ),
            },
            {
                'dest': '--batch',
                'kwargs': dict(action='store_true', help='No confirmation.'),
            },
        ],
    },
    {
        'action': ACTION_LIST,
        'help': 'List subscribed bangumi.',
    },
    {
        'action': ACTION_FILTER,
        'help': 'Set bangumi fetch filter.',
        'arguments': [
            {
                'dest': 'name',
                'kwargs': dict(metavar='name', help='Bangumi name to set the filter.'),
            },
            {
                'dest': '--subtitle',
                'kwargs': dict(metavar='subtitle', help='Subtitle group name, split by ",".'),
            },
            {
                'dest': '--include',
                'kwargs': dict(
                    metavar='include', help='Filter by keywords which in the title, split by ",".'
                ),
            },
            {
                'dest': '--exclude',
                'kwargs': dict(
                    metavar='exclude',
                    help='Filter by keywords which not int the title, split by ",".'
                ),
            },
            {
                'dest': '--regex',
                'kwargs': dict(metavar='regex', help='Filter by regular expression'),
            },
            {
                'dest': '--data-source',
                'kwargs': dict(metavar='data_source', help='Data source enabled, split by ","'),
            },
        ],
    },
    {
        'action': ACTION_UPDATE,
        'help': 'Update bangumi calendar and subscribed bangumi episode.',
        'arguments': [
            {
                'dest': 'name',
                'kwargs': dict(metavar='name', nargs='*', help='Update specified bangumi.'),
            },
            {
                'dest': ['--download', '-d'],
                'kwargs': dict(
                    action='store',
                    nargs='*',
                    type=int,
                    metavar='episode',
                    help='Download specified episode of the bangumi when updated.'
                ),
            },
            {
                'dest': '--not-ignore', 'kwargs': dict(
                    action='store_true',
                    help='Do not ignore the old bangumi detail rows (3 month ago).'
                )
            },
        ],
    },
    {
        'action': ACTION_CAL,
        'help': 'Print bangumi calendar.',
        'arguments': [
            {
                'dest': ['-s', '--show-source'],
                'kwargs': dict(action='store_true', help='Show bangumi data source.'),
            },
            {
                'dest': '--today',
                'kwargs': dict(action='store_true', help='Show bangumi calendar for today.'),
            },
            {
                'dest': ['-f', '--force-update'],
                'kwargs': dict(
                    action='store_true', help='Get the newest bangumi calendar from bangumi.moe.'
                ),
            },
            {
                'dest': '--download-cover',
                'kwargs': dict(action='store_true', help='Download the cover to local'),
            },
            {
                'dest': '--no-save', 'kwargs': dict(
                    action='store_true', help='Do not save the bangumi data when force update.'
                )
            },
        ],
    },
    {
        'action': ACTION_CONFIG,
        'help': 'Config BGmi.',
        'arguments': [
            {
                'dest': 'name',
                'kwargs': dict(
                    nargs='?',
                    help='Config name',
                    type=lambda s: s.upper(),
                    choices=bgmi.config.__all_writable_now__
                ),
            },
            {'dest': 'value', 'kwargs': dict(nargs='?', help='Config value')},
        ],
    },
    {
        'action': ACTION_MARK,
        'help': 'Mark bangumi episode.',
        'arguments': [
            {
                'dest': 'name',
                'kwargs': dict(help='Bangumi name'),
            },
            {
                'dest': 'episode',
                'kwargs': dict(help='Bangumi episode', type=int),
            },
        ],
    },
    {
        'action': ACTION_DOWNLOAD,
        'help': 'Download manager.',
        'arguments': [
            {
                'dest': '--list',
                'kwargs': dict(help='List download queue.', action='store_true'),
            },
            {
                'dest': '--mark',
                'kwargs': dict(
                    help='Mark download status with a specific id.', dest='id', type=int
                ),
            },
            {
                'dest': '--status',
                'kwargs': dict(
                    type=int,
                    help='Download items status (0: not download, 1: '
                    'downloading, 2: already downloaded).',
                    choices=[0, 1, 2],
                ),
            },
        ],
    },
    {
        'action': ACTION_FETCH,
        'help': 'Fetch bangumi.',
        'arguments': [
            {
                'dest': 'name',
                'kwargs': dict(help='Bangumi name', ),
            },
            {
                'dest': '--not-ignore',
                'kwargs': dict(
                    action='store_true',
                    help='Do not ignore the old bangumi detail rows (3 month ago).',
                ),
            },
        ],
    },
    {
        'action': ACTION_SEARCH,
        'help': 'Search torrents from data source by keyword',
        'arguments': [
            {
                'dest': 'keyword',
                'kwargs': dict(help='Search keyword', ),
            },
            {
                'dest': '--count',
                'kwargs': dict(type=int, help='The max page count of search result.'),
            },
            {
                'dest': '--regex-filter',
                'kwargs': dict(help='Regular expression filter of title.'),
            },
            {
                'dest': '--download',
                'kwargs': dict(action='store_true', help='Download search result.'),
            },
            {
                'dest': '--dupe',
                'kwargs': dict(action='store_true', help='Show duplicated episode'),
            },
            {
                'dest': '--min-episode',
                'kwargs': dict(
                    metavar='min_episode',
                    type=int,
                    help='Minimum episode filter of title.',
                ),
            },
            {
                'dest': '--max-episode',
                'kwargs': dict(
                    metavar='max_episode',
                    type=int,
                    help='Maximum episode filter of title.',
                ),
            },
        ],
    },
    {
        'action': ACTION_CONFIG_GEN,
        'help': 'Generate config for nginx',
        'arguments': [
            {
                'dest': 'config', 'kwargs': dict(
                    help='gen config file',
                    choices=[
                        'nginx.conf',
                        'bgmi_http.service',
                        'caddyfile',
                    ]
                )
            },
            {
                'dest': '--server-name',
                'kwargs': dict(metavar='server_name', help='nginx server name'),
            },
        ],
    },
    {
        'action': ACTION_COMPLETE,
        'help': 'Gen completion, `eval "$(bgmi complete)"` or `eval "$(bgmi complete|dos2unix)"`',
    },
    {
        'action': 'install',
        'help': 'Install BGmi front / admin / download delegate',
        'arguments': [
            {
                'dest': '--no-web',
                'kwargs': dict(
                    action='store_false', dest='install_web', help='Download web static file.'
                ),
            },
        ],
    },
    {
        'action': 'upgrade',
        'help': 'Check update.',
    },
    {
        'action': 'history',
        'help': 'List your history of following bangumi',
    },
]

__all__ = ['kv', 'actions_and_arguments', 'namespace']
