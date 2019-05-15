import json
from unittest import mock

from bgmi.website import get_all_provider
from bgmi.website.base import BaseWebsite


def w():
    return mock.Mock(spec=BaseWebsite)


def fetch_data():
    for key, value in get_all_provider():
        with open(
            './data/website/{}.fetch_bangumi_calendar_and_subtitle_group.json'.format(key),
            'w+',
            encoding='utf8'
        ) as f:
            json.dump(
                value.fetch_bangumi_calendar_and_subtitle_group(), f, indent=2, ensure_ascii=False
            )

        obj = {}
        for bangumi in value.get_bangumi_calendar_and_subtitle_group()[0]:
            obj[bangumi.keyword] = value.fetch_episode_of_bangumi(bangumi.keyword, max_page=1)[:3]
        with open('./data/website/{}.bangumi-episode.json'.format(key), 'w+', encoding='utf8') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)


class W(BaseWebsite):
    website_id = ''

    def __init__(self, website_id):
        self.website_id = website_id

    def fetch_bangumi_calendar_and_subtitle_group(self):
        with open(
            './tests/data/website/{}.fetch_bangumi_calendar_and_subtitle_group.json'.format(
                self.website_id
            ),
            'r',
            encoding='utf8'
        ) as f:
            return json.load(f)

    def fetch_episode_of_bangumi(self, bangumi_id, subtitle_list=None, max_page=1):
        with open(
            './tests/data/website/{}.bangumi-episode.json'.format(self.website_id),
            'r',
            encoding='utf8'
        ) as f:
            return json.load(f).get(bangumi_id, [])

    def search_by_keyword(self, keyword, count=None):
        episode_list = []

        with open(
            './tests/data/website/{}.bangumi-episode.json'.format(self.website_id),
            'r',
            encoding='utf8'
        ) as f:
            b = json.load(f)

        for li in b.values():
            for episode in li:
                if keyword in episode:
                    episode['name'] = keyword
                    episode_list.append(episode)
        return episode_list


MockDateSource = {key: W(website_id=key) for key in get_all_provider()}
