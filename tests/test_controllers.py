# coding=utf-8
from __future__ import print_function, unicode_literals

import os
import unittest

# from bgmi.cli import controllers, CONTROLLERS_DICT
from bgmi.controllers import add


class ModelsTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name = os.environ.get('BANGUMI_3')
        pass

    def tearDown(self):

        pass

    def test_add(self):
        add(self.bangumi_name, episode=3)

        pass
