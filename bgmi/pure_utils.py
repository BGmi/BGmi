from typing import List


def split_str_to_list(s: str) -> List[str]:
    result = []
    for x in s.split(','):
        ss = x.strip()
        if ss:
            result.append(ss)
    return result
