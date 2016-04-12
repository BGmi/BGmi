# coding=utf-8
from bgmi import __version__


def print_info(message):
    print('[*] %s' % message)


def print_success(message):
    print('\033[1;32m[+] %s\033[0m' % message)


def print_warning(message):
    print('\033[33m[-] %s\033[0m' % message)


def print_error(message):
    print('\033[1;31m[-] %s\033[0m' % message)
    exit(1)


def print_bilibili():
    print '''
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
           .coo:.         ;odo:.        |____/ \____| |_| |_| |_|_|\n''' % __version__


