# coding=utf-8
# Command Line Parser
import sys
from collections import OrderedDict


HELP = ('-h', '--help')


def _error(message):
    sys.stderr.write('error: %s\n' % message)
    exit(1)


class NameSpace(object):
    def __init__(self):
        self.__dict__['__value'] = {}

    def __setattr__(self, key, value):
        self.__value[key] = value

    def __getattr__(self, item):
        if item == '_NameSpace__value':
            return self.__dict__['__value']

        if item in self.__dict__['__value']:
            return self.__value[item]
        else:
            return self.__dict__[item]

    def __str__(self):
        return 'Namespace(\'%s\')' % str(self.__value)


class _CommandParserMixin(object):

    def _check_conflict(self, name):
        if name in self.arguments:
            _error('conflict argument name: %s' % name)

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
        elif arg.type == 's':
            # Sub parser
            # TODO: _(:3」∠)_ ooooooooh, strange
            return arg.group.sub
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

    def _get_positional_args(self):
        self.positional_args = [i for i in self.arguments.values()
                                if not i.optional and not i.type == 's']
        self._optional_args = [i for i in self.arguments.values()
                               if i not in self.positional_args and not i.type == 's']

        self._positional_args = self.positional_args[::-1]
        for i in self.arguments.values():
            if i.type == 's':
                self._sub_parser.update({i.name: i})

    def _parse_command(self, parser_group, _sys_args_list):
        while _sys_args_list:
            arg = _sys_args_list.pop()
            _mutex_arg = parser_group.mutex.get(arg, None)

            if _mutex_arg is not None:
                if arg in parser_group._mutex_list:
                    _error('arguments %s and %s are mutually exclusive' % (arg, _mutex_arg))
                parser_group._mutex_list.append(_mutex_arg)

            if arg in HELP:
                self.container.print_help()

            sub_parser = self._sub_parser.get(arg, None)
            if sub_parser:
                value = sub_parser.group.parse_command(sub_parser.name, _sys_args_list)
                arg_instance = sub_parser
                setattr(self.namespace, sub_parser.group.name, sub_parser.name)
            else:
                if arg.startswith('-'):
                    arg_instance = parser_group.arguments.get(arg, None)
                    if arg_instance is None:
                        _error('unrecognized arguments: %s' % arg)
                    else:
                        value = self._get_args(arg_instance, _sys_args_list)
                else:
                    # value = arg
                    if parser_group._positional_args:
                        arg_instance = parser_group._positional_args.pop()
                    else:
                        _error('unrecognized arguments: %s' % arg)
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
                    if value not in arg_instance.choice:
                        _error('unexpected choice of %s%s: %s' % (arg_instance.name,
                                                                  str(arg_instance.choice), value))
            setattr(self.namespace, arg_instance.dest, value)

        for arg in parser_group.arguments.values():
            if arg.required and self.namespace.__dict__['__value'].get(arg.dest) is None:
                _error('argument \'%s\' is required' % arg.name)


class ArgumentGroup(_CommandParserMixin):
    def __init__(self, name, help='', container=None):
        self.arguments = OrderedDict()
        self.name = name
        self.help = help
        self.container = container
        self.sub = self.argument_groups = {}
        self._sub_parser = {}
        self.mutex = {}
        self._mutex_list = []

    def add_argument(self, name, dest=None, arg_type=None, required=False, choice=None, default=None, mutex=None,
                     call=False, help='', hidden=False):
        self.container._check_conflict(name)
        argument = Argument(name=name, dest=dest, arg_type=arg_type, choice=choice,
                            default=default, call=call, help=help, group=self, required=required,
                            hidden=hidden)
        self.arguments.update({name: argument})

        # update mutex options dict

        if self.container.sub is None:
            self.container.arguments.update({name: argument})
            if mutex is not None:
                self.container.mutex.update({name: mutex, mutex: name})
        else:
            if mutex is not None:
                self.mutex.update({name: mutex, mutex: name})

    def add_sub_parser(self, name, help=None):
        if name in self.sub:
            _error('conflict sub parser name: %s' % name)
        sub_parser_group = ArgumentGroup(name=name, help=help, container=self)
        self.sub.update({name: sub_parser_group})
        self.add_argument(name=name, arg_type='s')
        return sub_parser_group

    def parse_command(self, sub_parser, _sys_args_list):
        self.namespace = NameSpace()
        sub_parser_group = self.sub.get(sub_parser, None)
        if sub_parser_group is None:
            return self.namespace

        ArgumentGroup._get_positional_args(sub_parser_group)
        sub_parser_group.namespace = self.namespace
        ArgumentGroup._set_default(sub_parser_group)

        # parse command
        self._parse_command(sub_parser_group, _sys_args_list)

        return self.namespace

    def print_help(self):
        return self.container.print_help()

    def __str__(self):
        return 'ArgumentGroup:<%s>' % self.name

    def __repr__(self):
        return 'ArgumentGroup:<%s>' % self.name


class Argument(object):
    args_type_list = ('+', '*', '1', None, 's')

    def __init__(self, name, dest, arg_type=None, choice=None, required=False, default=None, call=False,
                 help='', group=None, hidden=False):
        # check the validity of arg_type
        if arg_type not in self.args_type_list:
            _error('unexpected args type: %s' % arg_type)

        # positional arguments' argument type should be None
        if not name.startswith('-') and arg_type not in ('s', '+', None):
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

    def __init__(self):
        self._positional_args = []
        self._optional_args = []
        self.arguments = OrderedDict()
        self.argument_groups = {}
        self._sub_parser = {}
        self.mutex = {}
        self._mutex_list = []
        self.container = self

    def parse_command(self):
        self.sys_args = self._sys_args = sys.argv[1:][::-1]
        self.namespace = NameSpace()
        self._get_positional_args()
        self._set_default()

        self._parse_command(self, self._sys_args)
        return self.namespace

    def add_arg_group(self, name, help=''):
        group = ArgumentGroup(name=name, help=help, container=self)
        self.argument_groups.update({name: group})
        return group

    def print_help(self):
        self.sys_args = sys.argv[1:][::-1]

        def search(name):
            if name in self.arguments:
                ret = self.arguments.get(name)
                if not ret.type == 's':
                    return ret

            if name in self.argument_groups:
                return self.argument_groups.get(name)

            for group in self.argument_groups.values():
                if name in group.arguments:
                    ret = group.arguments.get(name)
                    if not ret.type == 's':
                        return ret

                if name in group.sub:
                    return group.sub.get(name)

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

        sys.stdout.write('\nUsage: \n')

        def _print_help(container, usage):
            container._get_positional_args()

            if container._positional_args:
                for arg in container._positional_args:
                    if not arg.hidden:
                        usage += get_arg_form(arg)

            if container._optional_args:
                usage += '[options] '

            if container.argument_groups:
                for arg in container.argument_groups.values():
                    if arg.argument_groups:
                        usage += '<%s> ' % arg.name

            sys.stdout.write('%s \n' % usage)

            if container.argument_groups:
                for group in container.argument_groups.values():
                    print_group_help(group)

            if container._positional_args:
                sys.stdout.write('\nCommands: \n')
                for arg in container._positional_args:
                    sys.stdout.write('  %-28s%s\n' % (arg.name, arg.help))

            if container._optional_args:
                sys.stdout.write('\nGeneral Options: \n')

            for arg in container._optional_args:
                form = get_arg_form(arg)
                if form:
                    sys.stdout.write('  %-28s%s\n' % (form, arg.help))

        arg = self.sys_args.pop() if self.sys_args else None
        ret = search(arg)

        usage = '  bgmi '
        if isinstance(ret, ArgumentGroup):
            usage += '%s ' % ret.name
            _print_help(ret, usage)
        else:
            _print_help(self, usage)

        exit(0)
