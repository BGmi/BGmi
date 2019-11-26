import inspect
import subprocess
from io import TextIOBase
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import List, TextIO, Union

from tornado import template


def split_str_to_list(s: str) -> List[str]:
    result = []
    for x in s.split(','):
        ss = x.strip()
        if ss:
            result.append(ss)
    return result


def exec_command(command: str) -> int:
    """
    exec command and stdout iconv
    :return: command exec result
    """
    status, stdout = subprocess.getstatusoutput(command)
    print(stdout)
    return status


def render_template(path_or_file: Union[str, Path, TextIOBase, TextIO], ctx: dict = None, **kwargs):
    """
    read file content and render it as tornado template with kwargs or ctx

    :param ctx:
    :param path_or_file: path-like or file-like object
    :param kwargs:
    :rtype: str
    :return:
    """
    if ctx and kwargs:
        raise ValueError('render_template and only be called with ctx or kwargs')
    # if hasattr(path_or_file, 'read'):
    if isinstance(path_or_file, TextIOBase):
        # input is a file
        content = path_or_file.read()
    else:
        # py3.4 can't open pathlib.Path directly, need to be str
        with open(str(path_or_file), 'r', encoding='utf8') as f:
            content = f.read()
    template_obj = template.Template(content, autoescape='')
    return template_obj.generate(**(ctx or kwargs)).decode('utf-8')


def parallel(func, args):
    """todo: need tests"""
    with ThreadPool(4) as pool:
        sign = inspect.signature(func)
        if len(sign.parameters) == 1:
            res = pool.starmap_async(func, ((x, ) for x in args))
        else:
            res = pool.starmap_async(func, args)
        return res.get()


def full_to_half(s):
    n = []
    # s = s.decode('utf-8')
    for char in s:
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:
            num -= 0xfee0
        num = chr(num)
        n.append(num)
    return ''.join(n)


def normalize_path(url):
    """
    normalize link to path

    :param url: path or url to normalize
    :type url: str
    :return: normalized path
    :rtype: str
    """
    url = url.replace('http://', 'http/').replace('https://', 'https/')
    illegal_char = [':', '*', '?', '"', '<', '>', '|', "'"]
    for char in illegal_char:
        url = url.replace(char, '')

    if url.startswith('/'):
        return url[1:]
    return url
