# coding=utf-8
import os
import shutil
import codecs
from setuptools import setup, find_packages
from setuptools.command.install import install
from bgmi import __version__, __author__, __email__
from bgmi.utils import print_warning, print_success, print_info

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


ROOT = os.path.abspath(os.path.dirname(__file__))


def long_description():
    with codecs.open('README.rst', 'r') as f:
        return f.read()


class CustomInstallCommand(install):
    def run(self):
        install.do_egg_install(self)
        home = os.environ.get('HOME', '')
        if not home:
            print_warning('$HOME not set, use \'/tmp/\'')
            home = '/tmp'

        bgmi_path = os.path.join(home, '.bgmi')
        if not os.path.exists(bgmi_path):
            print_success('%s created successfully' % bgmi_path)
            os.mkdir(bgmi_path)
        else:
            print_warning('%s are already exist' % bgmi_path)

        print_info('Installing crontab job')
        os.system('sh crontab.sh')
        print_info('Copy xunlei-lixian to %s' % bgmi_path)

        if not os.path.exists(os.path.join(bgmi_path, 'tools/xunlei-lixian')):
            os.mkdir(os.path.join(bgmi_path, 'tools'))
            shutil.copytree('tools/xunlei-lixian', os.path.join(bgmi_path, 'tools/xunlei-lixian'))
            print_info('Create link file')
            os.symlink(os.path.join(bgmi_path, 'tools/xunlei-lixian/lixian_cli.py'), os.path.join(bgmi_path, 'bgmi-lx'))
        else:
            print_warning('%s already exists' % os.path.join(bgmi_path, 'tools/xunlei-lixian'))


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
