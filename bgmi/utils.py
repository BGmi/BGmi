# coding=utf-8
import re
import datetime
import string
from bgmi import __version__
from bgmi.fetch import fetch
from bgmi.models import Bangumi, STATUS_FOLLOWED


def print_bilibili():
    print '''
            .cc          ,xc
             .kXO;      .xX0,
        .,;;;;:xKKd:;;:oKKKl:::;,.
       xOl;;;;;;;;,,,,,,,,,,,;:::dx.
      .O........................;.kl
      'k '                      ..do
      ,x ' 'kkOKOc      .xK0OOl ..do
      ,x ,    ;K;        'X:    ..oo
      ,x ,    ,X;        .K:    ..ol
      ;x ;     ,.        .c.    '.ol
      ,x :                      ..dl     ____   ____             _
      ,x l           .          ,.xc    | __ ) / ___|  _ __ ___ (_)
      .k;;'.....................,'O:    |  _ \| |  _  | '_ ` _ \| |
       .cddx'  ,doloooooodd.  ;xdd:     | |_) | |_| | | | | | | | |
           .coo:.         ;odo:.        |____/ \____| |_| |_| |_|_|

\t\t\t\t\t\t\t\t\033[1;33mversion''', __version__, '\033[0m\n'


def bangumi_calendar(force_update=False, today=False, followed=False, save=True):
    print_bilibili()
    if force_update:
        weekly_list = fetch(save=save)
    else:
        weekly_list = Bangumi.get_all_bangumi(status=STATUS_FOLLOWED if followed else None)

    if not weekly_list:
        print 'warning: no bangumi schedule, fetching ...'
        weekly_list = fetch(save=save)

    def shift(seq, n):
        n = n % len(seq)
        return seq[n:] + seq[:n]

    if today:
        weekday_order = (Bangumi.week[datetime.datetime.today().weekday()], )
    else:
        weekday_order = shift(Bangumi.week, datetime.datetime.today().weekday())

    spacial_append_chars = ['Ⅱ', 'Ⅲ', '♪']
    spacial_remove_chars = ['Δ', ]
    for index, weekday in enumerate(weekday_order):
        if weekly_list[weekday.lower()]:
            if index == 0:
                print '\033[1;37;42m%s.\033[0m' % weekday,
            else:
                print '\033[1;32m%s.\033[0m' % weekday,
            if not followed:
                print
                print '-' * 29, '+', '-' * 29, '+', '-' * 29, '+'

            for i, bangumi in enumerate(weekly_list[weekday.lower()]):
                if isinstance(bangumi['name'], unicode):
                    bangumi['name'] = bangumi['name'].encode('utf-8')
                half = len(re.findall('[%s]' % string.printable, bangumi['name']))
                full = (len(bangumi['name']) - half) / 3
                space_count = 28 - (full * 2 + half)

                for s in spacial_append_chars:
                    if s in bangumi['name']:
                        space_count += 1

                for s in spacial_remove_chars:
                    if s in bangumi['name']:
                        space_count -= 1
                if bangumi['status'] == str(STATUS_FOLLOWED):
                    bangumi['name'] = '\033[1;33m%s\033[0m' % bangumi['name']

                if followed:
                    if i > 0:
                        print ' ' * 4,
                    print bangumi['name'], bangumi['subtitle_group']
                else:
                    print bangumi['name'], ' ' * space_count, '|' if not followed else ' ',

                    if (i + 1) % 3 == 0:
                        print

            if not followed:
                print '\n'
        # print '\n', ' ' * 35, '|', ' ' * 35, '|'


if __name__ == '__main__':
    bangumi_calendar(force_update=False)
    # bangumi_calendar(force_update=True)
