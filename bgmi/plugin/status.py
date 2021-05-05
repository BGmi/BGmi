from enum import Enum


class DownloadStatus(Enum):
    not_downloading = 0
    downloading = 1
    done = 2
    error = 3
