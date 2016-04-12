# coding=utf-8
# Command Line Parser
import sys
from collections import OrderedDict


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
            if not arg.name.startswith('-'):
                value = None
            elif arg.default is not None:
                value = arg.default
            elif arg.type in ('+', '*', '1'):
                value = None
            elif arg.type is None:
                value = False
            elif arg.type == 's':
                value = {}
            else:
                _error('unexpected arg type: %s' % arg.type)

            setattr(self.namespace, arg.dest, value)

    def _get_positional_args(self):
        self.positional_args = [i for i in self.arguments.values()
                                if not i.name.startswith('-') and not i.type == 's']
        self._positional_args = self.positional_args[::-1]
        for i in self.arguments.values():
            if i.type == 's':
                self._sub_parser.update({i.name: i})

    def _parse_command(self, parser_group, _sys_args_list):
        while _sys_args_list:
            arg = _sys_args_list.pop()
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
                    value = arg
                    if parser_group._positional_args:
                        arg_instance = parser_group._positional_args.pop()
                    else:
                        _error('unrecognized arguments: %s' % arg)

                if arg_instance.choice:
                    if value not in arg_instance.choice:
                        _error('unrecognized choice %s%s: %s' % (arg_instance.name,
                                                                 str(arg_instance.choice), value))

            setattr(self.namespace, arg_instance.dest, value)


class ArgumentGroup(_CommandParserMixin):
    def __init__(self, name, desc='', container=None):
        self.arguments = OrderedDict()
        self.name = name
        self.desc = desc
        self.container = container
        self.sub = {}
        self._sub_parser = {}

    def add_argument(self, name, dest=None, arg_type=None, choice=None, default=None, call=False, help=''):
        self.container._check_conflict(name)
        argument = Argument(name=name, dest=dest, arg_type=arg_type, choice=choice,
                            default=default, call=call, help=help, group=self)
        self.arguments.update({name: argument})
        if self.container.sub is None:
            self.container.arguments.update({name: argument})

    def add_sub_parser(self, name, desc=None):
        if name in self.sub:
            _error('conflict sub parser name: %s' % name)
        sub_parser_group = ArgumentGroup(name=name, desc=desc, container=self)
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

    def __str__(self):
        return 'ArgumentGroup:<%s>' % self.name

    def __repr__(self):
        return 'ArgumentGroup:<%s>' % self.name


class Argument(object):
    args_type_list = ('+', '*', '1', None, 's')

    def __init__(self, name, dest, arg_type=None, choice=None, default=None, call=False, help='', group=None):
        # check the validity of arg_type
        if arg_type not in self.args_type_list:
            _error('unexpected args type: %s' % arg_type)

        # positional arguments' argument type should be None
        if not name.startswith('-') and arg_type not in ('s', None):
            _error('positional arguments expected argument type is \'None\'')

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

    def parse_command(self):
        self.sys_args = self._sys_args = sys.argv[1:][::-1]
        self.namespace = NameSpace()
        self._get_positional_args()
        self._set_default()

        self._parse_command(self, self._sys_args)
        return self.namespace

    def add_arg_group(self, name, desc=''):
        group = ArgumentGroup(name=name, desc=desc, container=self)
        self.argument_groups.update({name: group})
        return group

    def print_help(self):
        print 'Help'
