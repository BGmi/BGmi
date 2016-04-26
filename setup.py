# coding=utf-8
from setuptools import setup, find_packages
from bgmi import __version__, __author__, __email__

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

setup(
    name='bgmi',
    version=__version__,
    author=__author__,
    author_email=__email__,
    keywords='bangumi, bgmi, feed',
    description='subscribe bangumi!',
    url='https://github.com/RicterZ/BGmi',

    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'bgmi = bgmi.main'
        ]
    },
    license='MIT'
)
