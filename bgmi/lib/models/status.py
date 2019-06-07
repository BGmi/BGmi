from enum import IntEnum


class BangumiStatus(IntEnum):
    UPDATING = 0
    END = 1


class FollowedStatus(IntEnum):
    DELETED = 0
    FOLLOWED = 1
    UPDATED = 2
