# coding=utf-8
from __future__ import print_function
from bgmi import __version__
from bgmi.config import FETCH_URL


def print_info(message):
    print('[*] %s' % message)


def print_success(message):
    print('\033[1;32m[+] %s\033[0m' % message)


def print_warning(message):
    print('\033[33m[-] %s\033[0m' % message)


def print_error(message, exit_=True):
    print('\033[1;31m[x] %s\033[0m' % message)
    if exit_:
        exit(1)


def print_version():
    print('''BGmi \033[1;33mver. %s\033[0m built by \033[1;33mRicterZ\033[0m with ❤️

Github: https://github.com/RicterZ/BGmi
Email: ricterzheng@gmail.com
Blog: http://www.ricter.me''' % __version__)


def test_connection():
    import requests

    try:
        requests.head(FETCH_URL, timeout=5)
    except:
        return False

    return True


def unicodeize(data):
    import bgmi.config
    if bgmi.config.IS_PYTHON3:
        if isinstance(data, bytes):
            return data.decode('utf-8')
        else:
            return data
            # return bytes(str(data), 'latin-1').decode('utf-8')
    try:
        return unicode(data.decode('utf-8'))
    except UnicodeEncodeError:
        return data


def write_download_xml(data):
    import os
    file_path = os.path.join(os.path.dirname(__file__), '../download.xml')
    with open(file_path, 'w') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>')
        f.write('<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"'
                ' xmlns:wfw="http://wellformedweb.org/CommentAPI/">')
        f.write('<channel><title><![CDATA[BGmi Feed]]></title>')

        for i in data:
            f.write('<item>')
            f.write('<title><![CDATA[ %s ]]></title>' % i['title'].encode('utf-8'))
            f.write('<enclosure url="%s" length="1" type="application/x-bittorrent">'
                    '</enclosure>' % i['download'].encode('utf-8'))
            f.write('</item>')

        f.write('</channel></rss>')


def bug_report():
    print_error('It seems not any bangumi found, if http://dmhy.ricter.me can '
                'be opened normally, please report bug to ricterzheng@gmail.co'
                'm or submit issue at: https://github.com/RicterZ/BGmi/issues',
                exit_=False)
