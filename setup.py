# coding=utf-8
import os
import shutil
import codecs
from setuptools import setup, find_packages
from setuptools.command.install import install
from bgmi import __version__, __author__, __email__
from bgmi.setup import install_crontab, create_dir, install_xunlei_lixian

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


ROOT = os.path.abspath(os.path.dirname(__file__))


def long_description():
    with codecs.open('README.rst', 'r') as f:
        return f.read()


class CustomInstallCommand(install):
    def run(self):
        install.do_egg_install(self)
        install_crontab()
        create_dir()


setup(
    name='bgmi',
    version=__version__,
    author=__author__,
    author_email=__email__,
    keywords='bangumi, bgmi, feed',
    description='BGmi is a cli tool for subscribed bangumi.',
    long_description=long_description(),
    url='https://github.com/RicterZ/BGmi',
    download_url='https://github.com/RicterZ/BGmi/tarball/0.2',

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'bgmi = bgmi.main:setup',
        ]
    },
    license='MIT',
    cmdclass={'install': CustomInstallCommand},
)
