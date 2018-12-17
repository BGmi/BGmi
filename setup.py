# coding=utf-8
import os
import codecs
from setuptools import setup, find_packages
from bgmi import __version__, __author__, __email__


with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


ROOT = os.path.abspath(os.path.dirname(__file__))


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
    long_description_content_type='text/x-rst; charset=UTF-8',
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
    license='MIT License',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'Natural Language :: Chinese (Traditional)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ),
)
