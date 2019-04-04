# coding=utf-8
import os
from distutils import log
from distutils.command.clean import clean as _clean

from setuptools import setup, Command, find_packages

from bgmi import __version__, __author__, __email__

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

with open('requirements-test.txt', 'r') as f:
    test_requirements = f.read().splitlines()


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
        './*.egg-info', './__pycache__',
        "./.coverage"
    ]

    def run(self):

        """After calling the super class implementation, this function removes
        the directories specific to scikit-build."""

        from shutil import rmtree
        from glob import glob

        super(clean, self).run()
        for dirs in self.CLEAN_FILES:
            for glob_to_remove in glob(dirs):
                log.info("removing '%s'", glob_to_remove)
                if os.path.isdir(glob_to_remove):
                    rmtree(glob_to_remove)
                else:
                    os.remove(glob_to_remove)


packages = find_packages(exclude=('tests',))
log.info('find package %s', packages)
setup(
    version=__version__,
    author=__author__,
    author_email=__email__,
    install_requires=requirements,
    tests_require=test_requirements,
    packages=packages,
    cmdclass={
        'clean': clean,
        'test': TestCommand
    }
)
