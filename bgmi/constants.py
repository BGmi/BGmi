# coding=utf-8
from __future__ import print_function, unicode_literals

import sys

import bgmi.config
from bgmi.config import BANGUMI_MOE_URL, SHARE_DMHY_URL, unicode

ACTION_ADD = 'add'
ACTION_FETCH = 'fetch'
ACTION_FILTER = 'filter'
ACTION_DELETE = 'delete'
ACTION_UPDATE = 'update'
ACTION_CAL = 'cal'
ACTION_CONFIG = 'config'
ACTION_DOWNLOAD = 'download'
ACTION_FOLLOWED = 'followed'
ACTION_LIST = 'list'
ACTION_MARK = 'mark'
ACTION_SEARCH = 'search'
ACTION_SOURCE = 'source'
ACTIONS = (ACTION_ADD, ACTION_DELETE, ACTION_UPDATE, ACTION_CAL,
           ACTION_CONFIG, ACTION_FILTER, ACTION_FETCH, ACTION_DOWNLOAD, ACTION_FOLLOWED,
           ACTION_LIST, ACTION_MARK, ACTION_SEARCH, ACTION_SOURCE)

FILTER_CHOICE_TODAY = 'today'
FILTER_CHOICE_ALL = 'all'
FILTER_CHOICE_FOLLOWED = 'followed'
FILTER_CHOICES = (FILTER_CHOICE_ALL, FILTER_CHOICE_FOLLOWED, FILTER_CHOICE_TODAY)

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

DOWNLOAD_CHOICE = (DOWNLOAD_CHOICE_LIST_ALL, DOWNLOAD_CHOICE_LIST_DOWNLOADED,
                   DOWNLOAD_CHOICE_LIST_DOWNLOADING, DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD)

FOLLOWED_ACTION_LIST = 'list'
FOLLOWED_ACTION_MARK = 'mark'
FOLLOWED_CHOICE = (FOLLOWED_ACTION_LIST, FOLLOWED_ACTION_MARK)
SUPPORT_WEBSITE = [
    {
        'view': '萌番组 https://bangumi.moe/',
        'id': "bangumi_moe",
        'url': BANGUMI_MOE_URL
    },
    {
        'view': '蜜柑计划 https://mikanani.me/',
        'id': 'mikan_project',
        'url': 'https://mikanani.me/'
    },
    {
        'view': '动漫花园 http://share.dmhy.org/',
        'id': 'dmhy',
        'url': SHARE_DMHY_URL
    },
]
STATUS_SUCCESS = 'success'
STATUS_WARNING = 'warning'
STATUS_ERROR = 'error'
STATUS_INFO = 'info'

SPACIAL_APPEND_CHARS = ['Ⅱ', 'Ⅲ', '♪', 'Δ', '×', '☆', 'É', '·', '♭', '★']
SPACIAL_REMOVE_CHARS = []

UNSUPPORTED_VIDEO_CODING = ['hevc', ]
COMMON_EXCLUDE_KEYWORD = UNSUPPORTED_VIDEO_CODING


def unicode_(s):
    if not bgmi.config.IS_PYTHON3:
        unicode_string = s.decode(sys.getfilesystemencoding())
        return unicode_string
    else:
        return unicode(s)


actions_and_arguments = [
    {
        'action': ACTION_ADD,
        'help': 'Subscribe bangumi.',
        'arguments': {
            'name': dict(metavar='name', type=unicode_, nargs='+', help='Bangumi name'),
            '--episode': dict(metavar='episode', help='Add bangumi and mark it as specified episode.', type=int),
            '--not-ignore': dict(action='store_true', help='Do not ignore the old bangumi detail rows (3 month ago).'),
        }
    },
    {
        'action': ACTION_LIST,
        'help': 'List subscribed bangumi.',
    },
    {
        'action': ACTION_FILTER,
        'help': 'Set bangumi fetch filter.',
        'arguments': {
            'name': dict(metavar='name', type=unicode_, help='Bangumi name to set the filter.'),
            '--subtitle': dict(metavar='subtitle', type=unicode_, help='Subtitle group name, split by ",".'),
            '--include': dict(metavar='include', type=unicode_,
                              help='Filter by keywords which in the title, split by ",".'),
            '--exclude': dict(metavar='exclude', type=unicode_,
                              help='Filter by keywords which not int the title, split by ",".'),
            '--regex': dict(metavar='regex', type=unicode_, help='Filter by regular expression'),
        }
    },
    {
        'action': ACTION_UPDATE,
        'help': 'Update bangumi calendar and subscribed bangumi episode.',
        'arguments': {
            'name': dict(metavar='name', nargs='+', type=unicode_, help='Bangumi name to unsubscribe.'),

            '--download': dict(action='store', nargs='*', type=int, metavar='episode',
                               help='Download specified episode of the bangumi when updated.'),

            '--not-ignore': dict(action='store_true', help='Do not ignore the old bangumi detail rows (3 month ago).')
        }
    },
    {
        'action': ACTION_CAL,
        'help': 'Print bangumi calendar.',
        'arguments': {
            '--today': dict(action='store_true', help='Show bangumi calendar for today.'),

            '--force-update': dict(action='store_true', help='Get the newest bangumi calendar from bangumi.moe.'),

            '--download-cover': dict(action='store_true', help='Download the cover to local'),

            '--no-save': dict(action='store_true', help='Do not save the bangumi data when force update.')
        },

    },
    {
        'action': ACTION_CONFIG,
        'help': 'Config BGmi.',
        'arguments': {
            'name': dict(nargs='?', type=unicode_, help='Config name',
                         choices=bgmi.config.__writeable__ +
                                 bgmi.config.DOWNLOAD_DELEGATE_MAP[bgmi.config.DOWNLOAD_DELEGATE]),

            'value': dict(nargs='?', type=unicode_, help='Config value')
        },
    },
    {
        'action': ACTION_MARK,
        'help': 'Mark bangumi episode.',
        'arguments': {
            'name': dict(type=unicode_, help='Bangumi name'),

            'episode': dict(help='Bangumi episode', type=int)
        },
    },
    {
        'action': ACTION_DOWNLOAD,
        'help': 'Download manager.',
        'arguments': {
            '--list': dict(help='List download queue.', action='store_true'),
            '--mark': dict(help='Mark download status with a specific id.', dest='id', type=int),
            '--status': dict(type=int, help='Download items status (0: not download, 1: '
                                            'downloading, 2: already downloaded).',
                             choices=[0, 1, 2]),
        },
    },
    {
        'action': ACTION_FETCH,
        'help': 'Fetch bangumi.',
        'arguments': {
            'name': dict(help='Bangumi name', type=unicode_),

            '--not-ignore': dict(action='store_true',
                                 help='Do not ignore the old bangumi detail rows (3 month ago).'),
        },
    },
    {
        'action': ACTION_SEARCH,
        'arguments': {
            'keyword': dict(help='Search keyword', type=unicode_),
            '--count': dict(type=int, help='The max page count of search result.'),
            '--regex-filter': dict(type=unicode_, help='Regular expression filter of title.'),
            '--download': dict(action='store_true', help='Download search result.'),
            '--dupe': dict(action='store_true',
                           help="Show add result without filter and don't remove duplicated episode"),
        },
    },
    {
        'action': ACTION_SOURCE,
        'help': 'select date source bangumi_moe or mikan_project',
        'arguments': {
            'source': dict(help='bangumi_moe or mikan_project', type=unicode_,
                           choices=[x['id'] for x in SUPPORT_WEBSITE])
        }
    },
    {
        'action': 'install',
        'help': 'Install BGmi front / admin / download delegate'
    },
    {
        'action': 'upgrade',
        'help': 'Check update.'
    }

]
