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


def print_bilibili():
    print('''
            .cc          ,xc
             .kXO;      .xX0,
        .,;;;;:xKKd:;;:oKKKl:::;,.
       xOl;;;;;;;;,,,,,,,,,,,;:::dx.
      'k '                      ..do
      ,x ' 'kkOKOc      .xK0OOl ..do
      ,x ,    ;K;        'X:    ..oo
      ,x ,    ,X;        .K:    ..ol                    \033[1;33mversion %s\033[0m
      ;x ;     ,.        .c.    '.ol     ____   ____             _
      ,x l           .          ,.xc    | __ ) / ___|  _ __ ___ (_)
      .k;;'.....................,'O:    |  _ \| |  _  | '_ ` _ \| |
       .cddx'  ,doloooooodd.  ;xdd:     | |_) | |_| | | | | | | | |
           .coo:.         ;odo:.        |____/ \____| |_| |_| |_|_|\n''' % __version__)


def test_connection():
    import requests

    try:
        requests.head(FETCH_URL, timeout=5)
    except:
        return False

    return True
