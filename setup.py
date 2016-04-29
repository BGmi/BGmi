# coding=utf-8
from setuptools import setup, find_packages
from bgmi import __version__, __author__, __email__

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

def long_description():
    with open('README.md', 'r') as f:
        return f.read()

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
            'bgmi = bgmi.main:setup'
        ]
    },
    license='MIT',
    data_files=[
        ('', ['crontab.sh']),
    ]
)
