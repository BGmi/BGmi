from pkg_resources import get_distribution

from bgmi import config

__author__ = 'RicterZ'
__email__ = 'ricterzheng@gmail.com'
__version__ = get_distribution(__name__).version

__all__ = ['config']
