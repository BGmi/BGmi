import functools
import inspect
import os
import sys

from bgmi.logger import logger


def _dict_as_called(f, args, kwargs):
    """ return a dict of all the args and kwargs as the keywords they would
    be received in a real f call.  It does not call f.
    """

    names, args_name, kwargs_name, defaults, _, _, _ = inspect.getfullargspec(f)

    # assign basic args
    params = {}
    if args_name:
        basic_arg_count = len(names)
        params.update(zip(names[:], args))  # zip stops at shorter sequence
        params[args_name] = args[basic_arg_count:]
    else:
        params.update(zip(names, args))

    # assign kwargs given
    if kwargs_name:
        params[kwargs_name] = {}
        for kw, value in kwargs.items():
            if kw in names:
                params[kw] = value
            else:
                params[kwargs_name][kw] = value
    else:
        params.update(kwargs)

    # assign defaults
    if defaults:
        for pos, value in enumerate(defaults):
            if names[-len(defaults) + pos] not in params:
                params[names[-len(defaults) + pos]] = value

    return params


def log_utils_function(func):
    @functools.wraps(func)
    def echo_func(*func_args, **func_kwargs):
        r = func(*func_args, **func_kwargs)
        called_with = _dict_as_called(func, func_args, func_kwargs)
        logger.debug('util.%s %s -> `%s`', func.__name__, called_with, r)
        return r

    return echo_func


def disable_in_test(func):
    @functools.wraps(func)
    def echo_func(*func_args, **func_kwargs):
        if os.environ.get('UNITTEST'):
            return
        r = func(*func_args, **func_kwargs)
        return r

    return echo_func


GREEN = ''
YELLOW = ''
RED = ''
GREY = ''
WHITE = ''
COLOR_END = ''

if not sys.platform.startswith('win') or os.getenv('SHELL'):
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[1;31m'
    WHITE = '\033[1;37m'
    GREY = '\033[0m'
    COLOR_END = '\033[0m'

color_map = {
    'print_info': '',
    'print_success': GREEN,
    'print_warning': YELLOW,
    'print_error': RED,
}
indicator_map = {
    'print_info': '[*] ',
    'print_success': '[+] ',
    'print_warning': '[-] ',
    'print_error': '[x] ',
}


def _indicator(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('indicator', True):
            func_name = f.__qualname__
            args = (indicator_map.get(func_name, '') + args[0], )
        f(*args, **kwargs)
        sys.stdout.flush()

    return wrapper


def colorize(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        func_name = f.__qualname__
        b, e = color_map.get(func_name, ''), COLOR_END if color_map.get(func_name) else ''
        args = tuple(map(lambda s: b + s + e, args))
        return f(*args, **kwargs)

    return wrapper
