# coding: utf-8
from __future__ import print_function, unicode_literals
import unittest

from bgmi.utils import parse_episode


class ConfigTest(unittest.TestCase):
    def test_print_config(self):
        title = '[YMDR][哥布林殺手][Goblin Slayer][2018][01][1080p][AVC][JAP][BIG5][MP4-AAC][繁中]'
        self.assertEqual(1, parse_episode(title))
