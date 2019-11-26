from bgmi.utils.episode_parser import chinese_to_arabic, parse_episode


def test_parse_episode():
    with open('tests/data/episode', 'r', encoding='utf8') as f:
        lines = f.readlines()
        lines = map(lambda x: x.strip(), lines)
        lines = list(filter(bool, lines))
        lines = list(filter(lambda x: not x.startswith('#'), lines))

    for line in lines:
        episode, title = line.split(' ', 1)
        title = title.rstrip()
        episode = int(episode)
        assert episode == parse_episode(title), line

    return 0


def test_chinese_to_arabic():
    test_case = [
        ['二', 2],
        ['八', 8],
        ['十一', 11],
        ['一百二十三', 123],
        ['一千二百零三', 1203],
        ['一万一千一百零一', 11101],
    ]
    for raw, result in test_case:
        assert chinese_to_arabic(raw) == result, raw
