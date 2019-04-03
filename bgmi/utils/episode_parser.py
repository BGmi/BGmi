import re

from bgmi.logger import logger
from bgmi.utils.utils import log_utils_function


def chinese_to_arabic(cn: str) -> int:
    """
    https://blog.csdn.net/hexrain/article/details/52790126

    :type cn: str
    :rtype: int
    """
    CN_NUM = {
        '〇': 0,
        '一': 1,
        '二': 2,
        '三': 3,
        '四': 4,
        '五': 5,
        '六': 6,
        '七': 7,
        '八': 8,
        '九': 9,
        '零': 0,
        '壹': 1,
        '贰': 2,
        '叁': 3,
        '肆': 4,
        '伍': 5,
        '陆': 6,
        '柒': 7,
        '捌': 8,
        '玖': 9,
        '貮': 2,
        '两': 2,
    }

    CN_UNIT = {
        '十': 10,
        '拾': 10,
        '百': 100,
        '佰': 100,
        '千': 1000,
        '仟': 1000,
        '万': 10000,
        '萬': 10000,
    }
    unit = 0  # current
    ldig = []  # digest
    for cndig in reversed(cn):
        if cndig in CN_UNIT:
            unit = CN_UNIT.get(cndig)
            if unit in (10000, 100000000):
                ldig.append(unit)
                unit = 1
        else:
            dig = CN_NUM.get(cndig)
            if unit:
                dig *= unit
                unit = 0
            ldig.append(dig)
    if unit == 10:
        ldig.append(10)
    val, tmp = 0, 0
    for x in reversed(ldig):
        if x in (10000, 100000000):
            val += tmp * x
            tmp = 0
        else:
            tmp += x
    val += tmp
    return val


FETCH_EPISODE_WITH_BRACKETS = re.compile(r'[【\[](\d+)\s?(?:END)?[】\]]')

FETCH_EPISODE_ZH = re.compile(r"第?\s?(\d{1,3})\s?[話话集]")
FETCH_EPISODE_ALL_ZH = re.compile(r"第([^第]*?)[話话集]")
FETCH_EPISODE_ONLY_NUM = re.compile(r'^([\d]{2,})$')

FETCH_EPISODE_RANGE = re.compile(r'[\d]{2,}\s?-\s?([\d]{2,})')
FETCH_EPISODE_RANGE_ZH = re.compile(r'[第][\d]{2,}\s?-\s?([\d]{2,})\s?[話话集]')
FETCH_EPISODE_RANGE_ALL_ZH = re.compile(r'[全]([^-^第]*?)[話话集]')

FETCH_EPISODE_OVA_OAD = re.compile(r'([\d]{2,})\s?\((?:OVA|OAD)\)]')
FETCH_EPISODE_WITH_VERSION = re.compile(r'[【\[](\d+)\s? *v\d(?:END)?[】\]]')

FETCH_EPISODE = (FETCH_EPISODE_ZH, FETCH_EPISODE_ALL_ZH,
                 FETCH_EPISODE_WITH_BRACKETS, FETCH_EPISODE_ONLY_NUM,
                 FETCH_EPISODE_RANGE, FETCH_EPISODE_RANGE_ALL_ZH,
                 FETCH_EPISODE_OVA_OAD, FETCH_EPISODE_WITH_VERSION)


@log_utils_function
def parse_episode(episode_title):
    """
    parse episode from title

    :param episode_title: episode title
    :type episode_title: str
    :return: episode of this title
    :rtype: int
    """
    spare = None

    def get_real_episode(episode_list):
        episode_list = map(int, episode_list)
        real = min(episode_list)
        if real > 1900:
            return 0
        return real

    # check if range episode, return 0
    for regexp in [
            FETCH_EPISODE_RANGE_ALL_ZH, FETCH_EPISODE_RANGE,
            FETCH_EPISODE_RANGE_ZH
    ]:
        _ = regexp.findall(episode_title)
        if _ and _[0]:
            logger.debug('return episode range all zh')
            return int(0)

    _ = FETCH_EPISODE_ZH.findall(episode_title)
    if _ and _[0].isdigit():
        logger.debug('return episode zh')
        return int(_[0])

    _ = FETCH_EPISODE_ALL_ZH.findall(episode_title)
    if _ and _[0]:
        try:
            logger.debug('try return episode all zh %s', _)
            e = chinese_to_arabic(_[0])
            logger.debug('return episode all zh')
            return e
        except (ValueError, TypeError):
            logger.debug('can\'t convert %s to int', _[0])

    _ = FETCH_EPISODE_WITH_VERSION.findall(episode_title)
    if _ and _[0].isdigit():
        logger.debug('return episode range with version')
        return int(_[0])

    _ = FETCH_EPISODE_WITH_BRACKETS.findall(episode_title)
    if _:
        logger.debug('return episode with brackets')
        return get_real_episode(_)

    logger.debug('don\'t match any regex, try match after split')
    for i in episode_title.replace('[', ' ').replace('【', ',').split(' '):
        for regexp in FETCH_EPISODE:
            match = regexp.findall(i)
            if match and match[0].isdigit():
                match = int(match[0])
                if match > 1000:
                    spare = match
                else:
                    logger.debug('match %s %s %s', i, regexp, match)
                    return match

    if spare:
        return spare

    return 0
