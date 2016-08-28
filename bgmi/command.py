# coding=utf-8
# Command Line Parser
from __future__ import print_function, unicode_literals

import re
import sys
from collections import OrderedDict

from bgmi import __version__
from bgmi.utils.utils import unicodeize

HELP = ('-h', '--help')
JUST_GROUP = 0
SUB_PARSER = 1


def _error(message):
    sys.stderr.write('error: %s, try \'-h\' for help\n' % message)
    raise SystemExit(1)


class NameSpace(object):
    NameSpace_Action_Name = None

    def __init__(self):
        self.__dict__['__value'] = {}

    def __setattr__(self, key, value):
        if key == 'NameSpace_Action_Name':
            self.__dict__['NameSpace_Action_Name'] = value
        else:
            self.__value[key] = value

    def __getattr__(self, item):
        if item == '_NameSpace__value':
            return self.__dict__['__value']

        if item in self.__dict__['__value']:
            return self.__value[item]
        else:
            return self.__dict__[item]

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __str__(self):
        return 'Namespace(\'%s\')' % str(self.__value)

    def __repr__(self):
        return '\'%s\'' % self.__str__()

    def __eq__(self, other):
        return other == self.NameSpace_Action_Name


class _CommandParserMixin(object):

    def add_argument(self, name, dest=None, arg_type=None, required=False, choice=None, default=None, mutex=None,
                     call=False, help='', hidden=False):
        # self.container._check_conflict(name)
        self._check_conflict(name)
        argument = Argument(name=name, dest=dest, arg_type=arg_type, choice=choice,
                            default=default, call=call, help=help, group=self, required=required,
                            hidden=hidden)
        self.arguments.update({name: argument})

        # update mutex options dict
        if mutex is not None:
            self.mutex.update({name: mutex, mutex: name})

    def add_arg_group(self, name, help=''):
        self._check_group_conflict(name)
        group = ArgumentGroup(name=name, help=help, container=self)
        self.argument_groups.update({name: group})
        return group

    def _check_conflict(self, name):
        if name in self.arguments:
            _error('conflict argument name: %s' % name)

    def _check_group_conflict(self, name):
        if name in self.argument_groups:
            _error('conflict argument group name: %s' % name)

    def _check_group_name(self, name):
        if re.match('^([a-zA-Z0-9_]+)$', name) is None or re.match('^[0-9]', name):
            _error('invalid argument_name \'%s\'' % name)

    def _get_args(self, arg, _sys_args):
        '''Get argument(s) by arg_type
        '''
        if arg.type == '+':
            # One or more arguments
            if not _sys_args or _sys_args[-1].startswith('-'):
                _error('%s expected at least one argument' % arg.name)
            _arg_list = []
            while _sys_args and not _sys_args[-1].startswith('-'):
                _arg_list.append(_sys_args.pop())
            return _arg_list
        elif arg.type == '*':
            # Zero or more arguments
            raise NotImplementedError
        elif arg.type == '1':
            # Just one argument
            if not _sys_args:
                _error('%s expected one argument' % arg.name)
            return _sys_args.pop()
        elif arg.type is None:
            # None
            return True

    def _set_default(self):
        '''Set default value for each argument
        '''
        for arg in self.arguments.values():
            if arg.default is not None:
                value = arg.default
            else:
                value = None

            setattr(self.namespace, arg.dest, value)

        for group in self.argument_groups.values():
            group._set_default()
            setattr(self.namespace, group.name, group.namespace)

    def _get_positional_args(self):
        self.positional_args = [i for i in self.arguments.values()
                                if not i.optional and not i.type == 's']
        self._optional_args = [i for i in self.arguments.values()
                               if i not in self.positional_args and not i.type == 's']

        self._positional_args = self.positional_args[::-1]

    def _parse_command(self, parser_group, _sys_args_list):
        while _sys_args_list:
            arg = _sys_args_list.pop()
            _mutex_arg = parser_group.mutex.get(arg, None)

            if _mutex_arg is not None:
                if arg in parser_group._mutex_list:
                    _error('arguments %s and %s are mutually exclusive' % (arg, _mutex_arg))
                parser_group._mutex_list.append(_mutex_arg)

            if arg in HELP:
                parser_group.container.print_help()

            if arg.startswith('-'):
                arg_instance = parser_group.arguments.get(arg, None)
                if arg_instance is None:
                    if not parser_group.argument_groups:
                        _error('unrecognized arguments: %s' % arg)
                    _sys_args_list.append(arg)
                    break
                else:
                    value = self._get_args(arg_instance, _sys_args_list)
            else:
                if parser_group._positional_args:
                    arg_instance = parser_group._positional_args.pop()
                else:
                    if not parser_group.argument_groups:
                        _error('unrecognized arguments: %s' % arg)
                    _sys_args_list.append(arg)
                    break

                if arg_instance.type is None:
                    value = arg
                elif arg_instance.type == '+':
                    value = [arg]
                    for i in _sys_args_list[::-1]:
                        if not i.startswith('-'):
                            value.append(_sys_args_list.pop())
                        else:
                            break
                else:
                    _error('unsupported arg type: %s' % arg.type)

            if arg_instance.choice:
                if value not in map(str, arg_instance.choice):
                    _error('unexpected choice of %s (%s): %s' % (arg_instance.name,
                                                                 ', '.join(map(str, arg_instance.choice)), value))

            setattr(parser_group.namespace, arg_instance.dest, value)

        for arg in parser_group.arguments.values():
            if arg.required and parser_group.namespace.__dict__['__value'].get(arg.dest) is None:
                _error('argument \'%s\' is required' % arg.name)

        if isinstance(parser_group, ArgumentGroup):
            setattr(parser_group.container.namespace, parser_group.name, parser_group.namespace)


class ArgumentGroup(_CommandParserMixin):
    def __init__(self, name, help='', container=None, type=0):
        self.namespace = NameSpace()
        self.arguments = OrderedDict()
        self.name = name
        self.help = help
        self.container = container
        self.sub = self.argument_groups = OrderedDict()
        self.mutex = {}
        self._mutex_list = []
        # 0 - 普通的 group 我们普通的摇
        # 1 - sub parser group
        self.type = type

    def add_sub_parser(self, name, help=None):
        self._check_group_name(name)
        if name in self.argument_groups:
            _error('conflict sub parser name: %s' % name)
        sub_parser_group = ArgumentGroup(name=name, help=help, container=self, type=1)
        self.argument_groups.update({name: sub_parser_group})
        return sub_parser_group

    def parse_command(self, _sys_args_list):
        self._get_positional_args()
        self._set_default()

        self._parse_command(self, _sys_args_list)

        while _sys_args_list:
            arg = _sys_args_list.pop()

            sub_parser = self.argument_groups.get(arg, None)
            if not sub_parser:
                for group in self.argument_groups.values():
                    if arg in group.argument_groups:
                        sub_parser = group.argument_groups.get(arg)
                        break

            if sub_parser:
                sub_parser.parse_command(_sys_args_list)
                self.namespace.NameSpace_Action_Name = sub_parser.name
                break
            else:
                _error('unrecognized arguments: %s' % arg)

        return self.namespace

    def print_help(self):
        return self.container.print_help()

    def __str__(self):
        return 'ArgumentGroup:<%s>' % self.name

    def __repr__(self):
        return 'ArgumentGroup:<%s>' % self.name


class Argument(object):
    args_type_list = ('+', '*', '1', None)

    def __init__(self, name, dest, arg_type=None, choice=None, required=False, default=None, call=False,
                 help='', group=None, hidden=False):
        # check the validity of arg_type
        if arg_type not in self.args_type_list:
            _error('unexpected args type: %s' % arg_type)

        # positional arguments' argument type should be None
        if not name.startswith('-') and arg_type not in ('+', None):
            _error('unexpected positional argument type: %s' % arg_type)

        if not isinstance(choice, (list, tuple, set, str, type(None), )):
            _error('unexpected choice type: %s' % type(choice))

        # if dest not set, use name as dest
        if dest is None:
            if name.startswith('-'):
                _temp = name
                while _temp.startswith('-'):
                    _temp = _temp[1:]
                dest = _temp
            else:
                dest = name
            dest = dest.replace('-', '_')

        if arg_type == '*':
            raise NotImplementedError('not implemented arg type: *')

        self.name = name
        self.dest = dest
        self.type = arg_type
        self.call = call
        self.help = help
        self.default = default
        self.group = group
        self.choice = choice
        self.required = required
        self.hidden = hidden
        self.optional = self.name.startswith('-')

    def __str__(self):
        return 'Argument<\'%s\'>' % self.name

    def __repr__(self):
        return 'Argument<\'%s\'>' % self.name


class CommandParser(_CommandParserMixin):
    sub = None
    name = None

    def __init__(self):
        self.namespace = NameSpace()
        self._positional_args = []
        self._optional_args = []
        self.arguments = OrderedDict()
        self.argument_groups = OrderedDict()
        self.mutex = {}
        self._mutex_list = []
        self.container = self

    def parse_command(self):
        sys_argv = list(map(unicodeize, sys.argv))
        self.sys_args = self._sys_args = sys_argv[1:][::-1]
        self._get_positional_args()
        self._set_default()

        self._parse_command(self, self._sys_args)

        for group in self.argument_groups.values():
            group.parse_command(self._sys_args)

        return self.namespace

    def print_help(self):

        def search(name, group):
            if name in group.argument_groups:
                return group.argument_groups.get(name)
            else:
                for group in group.argument_groups.values():
                    if name in group.argument_groups:
                        return group.argument_groups.get(name)

        def get_arg_form(arg):
            if not arg.hidden:
                if arg.optional:
                    if arg.type == '+':
                        usage = '%s [%s ...]' % (arg.name, arg.dest.upper())
                    elif arg.type == '1':
                        usage = '%s %s' % (arg.name, arg.dest.upper())
                    elif arg.type is None:
                        usage = arg.name
                    else:
                        usage = ''
                else:
                    if arg.type == '+':
                        usage = '[%s] ... ' % arg.name
                    elif arg.type is None:
                        usage = '<%s> ' % arg.name
                    else:
                        usage = ''
                return usage
            else:
                return None

        def print_group_help(group):
            group._get_positional_args()
            if not group.positional_args and not group._optional_args and not group.sub:
                return

            group_name = group.name.title() if not group.name.startswith('-') else group.name
            sys.stdout.write('\n%s:\n' % group_name)

            for arg in group.arguments.values():
                usage = get_arg_form(arg)
                if usage:
                    sys.stdout.write('  %-28s%s\n' % (arg.name, arg.help))

            for sub in group.sub.values():
                sys.stdout.write('  %-28s%s\n' % (sub.name, sub.help))

        def _print_help(container, usage):
            container._get_positional_args()

            if container._positional_args:
                for arg in list(container._positional_args)[::-1]:
                    if not arg.hidden:
                        usage += get_arg_form(arg)

            if container._optional_args:
                usage += '[options] '

            if container.argument_groups:
                groups = [group.name for group in container.argument_groups.values() if group.type == JUST_GROUP]
                for group in container.argument_groups.values():
                    if group.type == SUB_PARSER:
                        groups.append('sub_commands')
                        break
                usage += '<{0}>'.format('|'.join(groups))

            sys.stdout.write('%s \n' % usage)

            if container.argument_groups:
                help_text = ''
                for group in list(container.argument_groups.values())[::-1]:
                    if group.type == SUB_PARSER:
                        help_text += '  %-28s%s\n' % (group.name, group.help)
                if help_text:
                    sys.stdout.write('\nSub Commands:\n')
                    sys.stdout.write(help_text)

                for group in list(container.argument_groups.values())[::-1]:
                    if group.type == JUST_GROUP:
                        print_group_help(group)

            if container._positional_args:
                sys.stdout.write('\nArguments: \n')
                for arg in container._positional_args[::-1]:
                    sys.stdout.write('  %-28s%s\n' % (arg.name, arg.help))

            if isinstance(container, ArgumentGroup):
                if container._optional_args:
                    sys.stdout.write('\nOptions: \n')

                for arg in container._optional_args:
                    form = get_arg_form(arg)
                    if form:
                        sys.stdout.write('  %-28s%s\n' % (form, arg.help))

            if self._optional_args:
                sys.stdout.write('\nGeneral Options: \n')

            for arg in self._optional_args:
                form = get_arg_form(arg)
                if form:
                    sys.stdout.write('  %-28s%s\n' % (form, arg.help))

        self.sys_args = sys.argv[1:][::-1]
        self._sys_args = sys.argv[1:]
        sys.stdout.write('BGmi %s (https://github.com/RicterZ/BGmi)\n\nUsage: \n' % __version__)

        arg_list = []
        while self.sys_args:
            arg = self.sys_args.pop()
            if arg not in HELP:
                arg_list.append(arg)
                break
        else:
            arg = None

        ret = search(arg, self)
        while ret and self.sys_args:
            arg = self.sys_args.pop()
            if arg not in HELP:
                _ = search(arg, ret)
                if _:
                    ret = _
                    arg_list.append(arg)

        usage = '  bgmi '
        if isinstance(ret, ArgumentGroup):
            usage += ' '.join(arg_list)
            usage += ' '
            _print_help(ret, usage)
        else:
            _print_help(self, usage)

        exit(0)
