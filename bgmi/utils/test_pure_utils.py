import os
import os.path
import shutil
import unittest.mock
from pathlib import Path

import pytest

import bgmi
import bgmi.config
import bgmi.utils.pure_utils
from bgmi.utils.pure_utils import split_str_to_list


@pytest.mark.parametrize(
    's, output', [
        ('1,2,3', ['1', '2', '3']),
        (' 1 , 2 , 3 ', ['1', '2', '3']),
        (' a , bbb , de ', ['a', 'bbb', 'de']),
    ]
)
def test_split_str_to_list(s, output):
    assert split_str_to_list(s) == output


def test_normalize_path():
    assert bgmi.utils.pure_utils.normalize_path(
        'http://hello? world:/233.qq'
    ) == 'http/hello world/233.qq'


class UtilsTest(unittest.TestCase):
    test_dir = './test_dir'

    def setUp(self):
        try:
            os.makedirs(self.test_dir)
        except FileExistsError:
            pass

    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except FileNotFoundError:
            pass

    @property
    def template_path(self) -> str:
        # print( os.path.join(self.test_dir, 'template.html'))
        return os.path.join(self.test_dir, 'template.html')

    def test_render_template_with_path(self):
        content = 'template content'
        with open(self.template_path, 'w+', encoding='utf8') as f:
            f.write(content)
        self.assertEqual(bgmi.utils.pure_utils.render_template(self.template_path), content)
        self.assertEqual(bgmi.utils.pure_utils.render_template(Path(self.template_path)), content)

    def test_render_template_with_file(self):
        content = 'template content'

        with open(self.template_path, 'w+', encoding='utf8') as f:
            f.write(content)
        with open(self.template_path, encoding='utf8') as f:
            self.assertEqual(bgmi.utils.pure_utils.render_template(f), content)

    def test_render_template_with_ctx(self):
        content = '{{name}} world'
        with open(self.template_path, 'w+', encoding='utf8') as f:
            f.write(content)
        with open(self.template_path, encoding='utf8') as f:
            self.assertEqual(
                bgmi.utils.pure_utils.render_template(f, ctx={'name': 'hello'}), 'hello world'
            )

    def test_render_template_with_kwargs(self):
        content = '{{name}} world'
        with open(self.template_path, 'w+', encoding='utf8') as f:
            f.write(content)
        with open(self.template_path, encoding='utf8') as f:
            self.assertEqual(bgmi.utils.pure_utils.render_template(f, name='hello'), 'hello world')
