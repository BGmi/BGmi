from typing import List

from bgmi.config import cfg

ACTION_ADD = "add"
ACTION_FETCH = "fetch"
ACTION_FILTER = "filter"
ACTION_DELETE = "delete"
ACTION_UPDATE = "update"
ACTION_CAL = "cal"
ACTION_CONFIG = "config"
ACTION_DOWNLOAD = "download"
ACTION_LIST = "list"
ACTION_MARK = "mark"
ACTION_SEARCH = "search"
ACTION_SOURCE = "source"
ACTION_CONFIG_GEN = "gen"
ACTION_COMPLETE = "complete"  # bash completion
ACTIONS = (
    ACTION_ADD,
    ACTION_DELETE,
    ACTION_UPDATE,
    ACTION_CAL,
    ACTION_CONFIG,
    ACTION_FILTER,
    ACTION_FETCH,
    ACTION_DOWNLOAD,
    ACTION_LIST,
    ACTION_MARK,
    ACTION_SEARCH,
    ACTION_SOURCE,
    ACTION_COMPLETE,
)
ACTION_FOLLOWED = "followed"  # place holder?
ACTION_HISTORY = "history"

FILTER_CHOICE_TODAY = "today"
FILTER_CHOICE_ALL = "all"
FILTER_CHOICE_FOLLOWED = "followed"
FILTER_CHOICES = (FILTER_CHOICE_ALL, FILTER_CHOICE_FOLLOWED, FILTER_CHOICE_TODAY)

DOWNLOAD_ACTION_LIST = "list"
DOWNLOAD_ACTION_MARK = "mark"
DOWNLOAD_ACTION = (DOWNLOAD_ACTION_LIST, DOWNLOAD_ACTION_MARK)

DOWNLOAD_CHOICE_LIST_ALL = "all"
DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD = "not_downloaded"
DOWNLOAD_CHOICE_LIST_DOWNLOADING = "downloading"
DOWNLOAD_CHOICE_LIST_DOWNLOADED = "downloaded"
DOWNLOAD_CHOICE_LIST_DICT = {
    None: DOWNLOAD_CHOICE_LIST_ALL,
    0: DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD,
    1: DOWNLOAD_CHOICE_LIST_DOWNLOADING,
    2: DOWNLOAD_CHOICE_LIST_DOWNLOADED,
}

DOWNLOAD_CHOICE = (
    DOWNLOAD_CHOICE_LIST_ALL,
    DOWNLOAD_CHOICE_LIST_DOWNLOADED,
    DOWNLOAD_CHOICE_LIST_DOWNLOADING,
    DOWNLOAD_CHOICE_LIST_NOT_DOWNLOAD,
)

FOLLOWED_ACTION_LIST = "list"
FOLLOWED_ACTION_MARK = "mark"
FOLLOWED_CHOICE = (FOLLOWED_ACTION_LIST, FOLLOWED_ACTION_MARK)
SUPPORT_WEBSITE = [
    {"view": "萌番组 https://bangumi.moe/", "id": "bangumi_moe", "url": cfg.bangumi_moe_url},
    {
        "view": "蜜柑计划 https://mikanani.me/",
        "id": "mikan_project",
        "url": "https://mikanani.me/",
    },
    {"view": "动漫花园 http://share.dmhy.org/", "id": "dmhy", "url": cfg.share_dmhy_url},
]
STATUS_SUCCESS = "success"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"
STATUS_INFO = "info"

SPACIAL_APPEND_CHARS = ["Ⅱ", "Ⅲ", "♪", "Δ", "×", "☆", "É", "·", "♭", "★"]
SPACIAL_REMOVE_CHARS: List[str] = []

UNSUPPORTED_VIDEO_CODING = [
    "hevc",
]
COMMON_EXCLUDE_KEYWORD = UNSUPPORTED_VIDEO_CODING

# There should be no `'` in any help message
actions_and_arguments: List[dict] = [
    {
        "action": ACTION_ADD,
        "help": "Subscribe bangumi.",
        "arguments": [
            {
                "dest": "name",
                "kwargs": {"metavar": "name", "type": str, "nargs": "+", "help": "Bangumi name"},
            },
            {
                "dest": "--episode",
                "kwargs": {"metavar": "episode", "help": "Add bangumi and mark it as specified episode.", "type": int},
            },
            {
                "dest": "--not-ignore",
                "kwargs": {"action": "store_true", "help": "Do not ignore the old bangumi detail rows (3 month ago)."},
            },
        ],
    },
    {
        "action": ACTION_DELETE,
        "help": "Unsubscribe bangumi.",
        "arguments": [
            {
                "dest": "--name",
                "kwargs": {"metavar": "name", "nargs": "+", "type": str, "help": "Bangumi name to unsubscribe."},
            },
            {
                "dest": "--clear-all",
                "kwargs": {
                    "action": "store_true",
                    "help": "Clear all the subscriptions, name will be ignored If you " "provide this flag.",
                },
            },
            {
                "dest": "--batch",
                "kwargs": {"action": "store_true", "help": "No confirmation."},
            },
        ],
    },
    {"action": ACTION_LIST, "help": "List subscribed bangumi."},
    {
        "action": ACTION_FILTER,
        "help": "Set bangumi fetch filter.",
        "arguments": [
            {
                "dest": "name",
                "kwargs": {"metavar": "name", "type": str, "help": "Bangumi name to set the filter."},
            },
            {
                "dest": "--subtitle",
                "kwargs": {"metavar": "subtitle", "type": str, "help": 'Subtitle group name, split by ",".'},
            },
            {
                "dest": "--include",
                "kwargs": {
                    "metavar": "include",
                    "type": str,
                    "help": 'Filter by keywords which in the title, split by ",".',
                },
            },
            {
                "dest": "--exclude",
                "kwargs": {
                    "metavar": "exclude",
                    "type": str,
                    "help": 'Filter by keywords which not int the title, split by ",".',
                },
            },
            {
                "dest": "--regex",
                "kwargs": {"metavar": "regex", "type": str, "help": "Filter by regular expression"},
            },
        ],
    },
    {
        "action": ACTION_UPDATE,
        "help": "Update bangumi calendar and subscribed bangumi episode.",
        "arguments": [
            {
                "dest": "name",
                "kwargs": {"metavar": "name", "type": str, "nargs": "*", "help": "Update specified bangumi."},
            },
            {
                "dest": ["--download", "-d"],
                "kwargs": {
                    "action": "store",
                    "nargs": "*",
                    "type": int,
                    "metavar": "episode",
                    "help": "Download specified episode of the bangumi when updated.",
                },
            },
            {
                "dest": "--not-ignore",
                "kwargs": {"action": "store_true", "help": "Do not ignore the old bangumi detail rows (3 month ago)."},
            },
        ],
    },
    {
        "action": ACTION_CAL,
        "help": "Print bangumi calendar.",
        "arguments": [
            {
                "dest": "--today",
                "kwargs": {"action": "store_true", "help": "Show bangumi calendar for today."},
            },
            {
                "dest": ["-f", "--force-update"],
                "kwargs": {"action": "store_true", "help": "Get the newest bangumi calendar from current data source."},
            },
            {
                "dest": "--download-cover",
                "kwargs": {"action": "store_true", "help": "Download the cover to local"},
            },
            {
                "dest": "--no-save",
                "kwargs": {"action": "store_true", "help": "Do not save the bangumi data when force update."},
            },
        ],
    },
    {
        "action": ACTION_CONFIG,
        "help": "Show bgmi config.",
        "arguments": [
            {
                "dest": "name",
                "kwargs": {
                    "nargs": "?",
                    "type": str,
                    "help": "Config name",
                },
            },
            {
                "dest": "value",
                "kwargs": {"nargs": "?", "type": str, "help": "Config value"},
            },
        ],
    },
    {
        "action": ACTION_MARK,
        "help": "Mark bangumi episode.",
        "arguments": [
            {"dest": "name", "kwargs": {"type": str, "help": "Bangumi name"}},
            {"dest": "episode", "kwargs": {"help": "Bangumi episode", "type": int}},
        ],
    },
    {
        "action": ACTION_DOWNLOAD,
        "help": "Download manager.",
        "arguments": [
            {
                "dest": "--list",
                "kwargs": {"help": "List download queue.", "action": "store_true"},
            },
            {
                "dest": "--mark",
                "kwargs": {"help": "Mark download status with a specific id.", "dest": "id", "type": int},
            },
            {
                "dest": "--status",
                "kwargs": {
                    "type": int,
                    "help": "Download items status (0: not download, 1: " "downloading, 2: already downloaded).",
                    "choices": [0, 1, 2],
                },
            },
        ],
    },
    {
        "action": ACTION_FETCH,
        "help": "Fetch bangumi.",
        "arguments": [
            {"dest": "name", "kwargs": {"help": "Bangumi name", "type": str}},
            {
                "dest": "--not-ignore",
                "kwargs": {"action": "store_true", "help": "Do not ignore the old bangumi detail rows (3 month ago)."},
            },
        ],
    },
    {
        "action": ACTION_SEARCH,
        "help": "Search torrents from data source by keyword",
        "arguments": [
            {"dest": "keyword", "kwargs": {"help": "Search keyword", "type": str}},
            {
                "dest": "--count",
                "kwargs": {"type": int, "help": "The max page count of search result."},
            },
            {
                "dest": "--regex-filter",
                "kwargs": {"type": str, "help": "Regular expression filter of title."},
            },
            {
                "dest": "--download",
                "kwargs": {"action": "store_true", "help": "Download search result."},
            },
            {
                "dest": "--dupe",
                "kwargs": {"action": "store_true", "help": "Show duplicated episode"},
            },
            {
                "dest": "--min-episode",
                "kwargs": {"metavar": "min_episode", "type": int, "help": "Minimum episode filter of title."},
            },
            dict(dest="--tag", kwargs=dict(action="store_true", help="Use tag to search")),
            {
                "dest": "--subtitle",
                "kwargs": {"type": str, "help": "Subtitle group filter of title (Need --tag enabled)"},
            },
            {
                "dest": "--max-episode",
                "kwargs": {"metavar": "max_episode", "type": int, "help": "Maximum episode filter of title."},
            },
        ],
    },
    {
        "action": ACTION_SOURCE,
        "help": "Select date source bangumi_moe or mikan_project",
        "arguments": [
            {
                "dest": "source",
                "kwargs": {
                    "help": "bangumi_moe or mikan_project",
                    "type": str,
                    "choices": [x["id"] for x in SUPPORT_WEBSITE],
                },
            },
        ],
    },
    {
        "action": ACTION_CONFIG_GEN,
        "help": "Generate config for nginx",
        "arguments": [
            {
                "dest": "config",
                "kwargs": {"help": "gen nginx.conf", "type": str, "choices": ["nginx.conf"]},
            },
            {
                "dest": "--server-name",
                "kwargs": {"metavar": "server_name", "help": "server name", "type": str, "required": True},
            },
        ],
    },
    {"action": "install", "help": "Install BGmi front / admin / download delegate"},
    {"action": "upgrade", "help": "Check update."},
    {"action": "history", "help": "List your history of following bangumi"},
]

BANGUMI_UPDATE_TIME = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Unknown")
