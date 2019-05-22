from . import kv
from .actions import ACTION_DOWNLOAD

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
]


class NameSpace:
    data_source_provider = 'bgmi.data_source.provider'
    download_delegate = 'bgmi.downloader.delegate'


__all__ = (
    'kv', 'actions_and_arguments', 'NameSpace', 'SPACIAL_APPEND_CHARS', 'SPACIAL_REMOVE_CHARS',
    'SECOND_OF_WEEK'
)
