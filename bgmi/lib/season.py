"""Parse and normalize season information in bangumi titles."""

import re
from typing import Dict

CN_NUM_MAP: Dict[str, int] = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
    "十三": 13,
    "十四": 14,
    "十五": 15,
}


def _cn_to_int(s: str) -> int:
    if s in CN_NUM_MAP:
        return CN_NUM_MAP[s]
    if s.startswith("十"):
        return 10 + _cn_to_int(s[1:])
    if s.endswith("十"):
        return _cn_to_int(s[:-1]) * 10
    return 1


SEASON_PATTERNS = [
    # 第2季, 第02季
    (r"第\s*(\d+)\s*季", None),
    # 第二季, 第十二季
    (r"第\s*([一二三四五六七八九十]+)\s*季", _cn_to_int),
    # Season 2, Season02
    (r"[Ss]eason\s*(\d+)", None),
    # S2, S02 (standalone, not part of a longer word)
    (r"(?<![a-zA-Z])S(\d+)(?![a-zA-Z\d])", None),
    # 2nd Season, 3rd Season
    (r"(\d+)(?:st|nd|rd|th)\s*[Ss]eason", None),
    # Part 2, Part II (less reliable, lower priority)
    (r"Part\s*(\d+)", None),
]


def parse_season(name: str) -> int:
    """Parse season number from a bangumi name. Returns 1 if not detected."""
    for pattern, converter in SEASON_PATTERNS:
        m = re.search(pattern, name)
        if m:
            raw = m.group(1)
            if converter:
                return converter(raw)
            return int(raw)
    return 1


def strip_season_suffix(name: str) -> str:
    """Remove a trailing season marker from a bangumi name."""
    trailing_patterns = [
        r"第\s*\d+\s*季",
        r"第\s*[一二三四五六七八九十]+\s*季",
        r"[Ss]eason\s*\d+",
        r"(?<![a-zA-Z])S\d+(?![a-zA-Z\d])",
        r"\d+(?:st|nd|rd|th)\s*[Ss]eason",
        r"Part\s*\d+",
    ]
    separator = r"(?:[\s._\-:：/／|｜]+)?"
    for pattern in trailing_patterns:
        stripped = re.sub(rf"{separator}{pattern}\s*$", "", name)
        if stripped != name:
            return stripped.strip()
    return name
