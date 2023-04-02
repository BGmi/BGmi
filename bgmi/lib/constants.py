from typing import List

SUPPORT_WEBSITE = [
    {"view": "萌番组 https://bangumi.moe/", "id": "bangumi_moe"},
    {"view": "蜜柑计划 https://mikanani.me/", "id": "mikan_project"},
    {
        "view": "动漫花园 http://share.dmhy.org/",
        "id": "dmhy",
    },
]

SPACIAL_APPEND_CHARS = ["Ⅱ", "Ⅲ", "♪", "Δ", "×", "☆", "É", "·", "♭", "★"]
SPACIAL_REMOVE_CHARS: List[str] = []

BANGUMI_UPDATE_TIME = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Unknown")
