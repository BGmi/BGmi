# coding=utf-8
import codecs
import os
import sys

from setuptools import setup, find_packages, Command

from bgmi import __version__, __author__, __email__

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()
    if sys.version_info[1] < 5:
        requirements.append('typing')

with open('test_requirements.txt', 'r') as f:
    test_requirements = f.read().splitlines()

from distutils.command.clean import clean as _clean


class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import unittest

        os.environ['UNITTEST'] = '1'
        test_loader = unittest.defaultTestLoader
        test_runner = unittest.TextTestRunner(verbosity=True)
        test_suite = test_loader.discover('.')
        test_runner.run(test_suite)


class clean(_clean):
    """Custom implementation of ``clean`` setuptools command."""
    CLEAN_FILES = [
        './build', './dist',
        './*.pyc', './*.tgz',
        './*.egg-info', './__pycache__'
    ]

    def run(self):

        """After calling the super class implementation, this function removes
        the directories specific to scikit-build."""

        from distutils import log
        from shutil import rmtree
        from glob import glob

        super(clean, self).run()
        for dirs in self.CLEAN_FILES:
            for dir in glob(dirs):
                log.info("removing '%s'", dir)
                rmtree(dir)


def long_description():
    with codecs.open('README.rst', 'rb') as f:
        return f.read().decode('utf-8')


setup(
    name='bgmi',
    version=__version__,
    author=__author__,
    author_email=__email__,
    keywords='bangumi, bgmi, feed',
    description='BGmi is a cli tool for subscribed bangumi.',
    long_description=long_description(),
    long_description_content_type='text/x-rst',
    url='https://github.com/BGmi/BGmi',
    download_url='https://github.com/BGmi/BGmi/tarball/master',
    packages=find_packages(),
    package_data={'': ['LICENSES']},
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'bgmi = bgmi.main:main',
            'bgmi_http = bgmi.front.server:main'
        ]
    },
    extras_require={
        'mysql': ["pymysql", ],
    },
    license='MIT License',
    tests_require=test_requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'Natural Language :: Chinese (Traditional)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    cmdclass={
        'clean': clean,
        'test': TestCommand
    }
)
