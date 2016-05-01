# coding=utf-8
import sys
import unittest
from bgmi.command import CommandParser, NameSpace


class CommandTest(unittest.TestCase):

    def test_argument_name(self):
        c = CommandParser()
        group_1 = c.add_arg_group('test')
        group_1.add_argument('--id-aa--', arg_type='1')
        sys.argv = ['test.py', '--id-aa--', '123456']
        namespace_1 = c.parse_command()

        self.assertEqual(namespace_1.test.id_aa__, '123456')

    def test_parse_positional_argument(self):
        c = CommandParser()
        c.add_argument('method')
        c.add_argument('sub_method')
        sys.argv = ['test.py', 'method_test', 'sub_method_test']
        namespace_1 = c.parse_command()

        self.assertEqual(namespace_1.method, 'method_test')
        self.assertEqual(namespace_1.sub_method, 'sub_method_test')

    def test_sub_parser(self):
        c = CommandParser()
        group_1 = c.add_arg_group('test')
        sub_1 = group_1.add_sub_parser('sub_action')
        sub_2 = group_1.add_sub_parser('sub_action2')

        # conflict action name: --sub_action
        self.assertRaises(SystemExit, group_1.add_sub_parser, '--sub_action')

        sub_1.add_argument('--force')
        sub_1.add_argument('--id', arg_type='+')
        sub_2.add_argument('--verbose', arg_type='+')

        sys.argv = ['test.py', 'sub_action', '--force']
        namespace_1 = c.parse_command()
        self.assertEqual(namespace_1.test.sub_action.force, True)

        sys.argv = ['test.py', 'sub_action', '--force', '--sub_action2', '--verbose', '1']
        # unrecognized arguments: --sub_action2
        self.assertRaises(SystemExit, c.parse_command)

        sys.argv = ['test.py', 'sub_action2', '--force']
        # unrecognized arguments: --force
        self.assertRaises(SystemExit, c.parse_command)
        sys.argv = ['test.py', 'sub_action2', '--verbose', '666']
        namespace_1 = c.parse_command()
        self.assertEqual(namespace_1.test.sub_action2.verbose, ['666', ])

        d = CommandParser()
        group_2 = d.add_arg_group('action')
        s_1 = group_2.add_sub_parser('update')
        s_1.add_argument('subaction')
        s_2 = group_2.add_sub_parser('delete')
        s_2.add_argument('--subaction2')

        sys.argv = ['test.py', 'update', 'help']
        namespace_2 = d.parse_command()
        self.assertEqual(namespace_2.action.update.subaction, 'help')

        sys.argv = ['test.py', 'delete', '--subaction2']
        namespace_2 = d.parse_command()
        self.assertEqual(namespace_2.action.delete.subaction2, True)

    def test_parse_command(self):
        c = CommandParser()
        group_1 = c.add_arg_group('test')
        # positional argument
        group_1.add_argument('method')
        group_1.add_argument('-v', dest='verbose', default=False)
        group_1.add_argument('--id', dest='id', arg_type='1', default=False)
        group_1.add_argument('--id2', dest='id2', arg_type='+')
        group_1.add_argument('--id3', dest='id3', arg_type='+')

        sys.argv = ['test.py', 'method_test1']
        namespace_1 = c.parse_command()
        self.assertFalse(namespace_1.test.verbose)

        sys.argv = ['test.py', 'method_test2', '-v']
        namespace_2 = c.parse_command()
        self.assertTrue(namespace_2.test.verbose)

        sys.argv = ['test.py', 'method_test3', '-v', '--id', '1', '--id2', '1', '2']
        namespace_3 = c.parse_command()
        self.assertEqual(namespace_3.test.method, 'method_test3')
        self.assertEqual(namespace_3.test.id, '1')
        self.assertEqual(namespace_3.test.id2, ['1', '2'])

    def test_choice(self):
        c = CommandParser()
        g1 = c.add_arg_group('test')
        g1.add_argument('--method', arg_type='1', choice=('GET', 'POST', 'HEAD', ))
        sys.argv = ['test.py', '--method', 'PUT']
        self.assertRaises(SystemExit, c.parse_command)

        c = CommandParser()
        g2 = c.add_arg_group('test')
        sub_1 = g2.add_sub_parser('get_method')
        sub_1.add_argument('--get', arg_type='1', choice=('GET', 'HEAD', ), default='GET')

        sub_2 = g2.add_sub_parser('post_method')
        sub_2.add_argument('--post', arg_type='1', choice=('POST', 'PUT', ))

        sys.argv = ['test.py', 'get_method']
        namespace = c.parse_command()
        self.assertEqual(namespace.test.get_method.get, 'GET')

    def test_required(self):
        c = CommandParser()
        g1 = c.add_arg_group('test')
        g1.add_argument('method', required=True)
        g1.add_argument('--get', required=True)

        sys.argv = ['test.py']
        self.assertRaises(SystemExit, c.parse_command)

        sys.argv = ['test.py', 'GET']
        self.assertRaises(SystemExit, c.parse_command)

        sys.argv = ['test.py', 'GET', '--get']
        self.assertIsInstance(c.parse_command(), NameSpace)

    def test_position_arg_type(self):
        c = CommandParser()
        g1 = c.add_arg_group('test')
        g1.add_argument('position', arg_type='+')
        g1.add_argument('--verbose')
        sys.argv = ['test.py', 'AAA', 'BBB', 'CCC', '--verbose']
        namespace = c.parse_command()
        self.assertEqual(namespace.test.position, ['AAA', 'BBB', 'CCC'])

    def test_mutex_arg(self):
        # ordinary
        c = CommandParser()
        g1 = c.add_arg_group('test')
        g1.add_argument('--clear-all', mutex='--delete')
        g1.add_argument('--delete', arg_type='+')
        sys.argv = ['test.py', '--delete', 'AAA', '--clear-all']
        self.assertRaises(SystemExit, c.parse_command)

        # sub parser
        c = CommandParser()
        g2 = c.add_arg_group('test')
        sub = g2.add_sub_parser('sub')
        sub.add_argument('--clear-all', mutex='--delete')
        sub.add_argument('--delete', arg_type='+')
        sys.argv = ['test.py', 'sub', '--delete', 'AAA', '--clear-all']
        self.assertRaises(SystemExit, c.parse_command)

        c = CommandParser()
        g3 = c.add_arg_group('test')
        g3.add_argument('--clear-all-sub', mutex='--delete-sub')
        sub2 = g3.add_sub_parser('sub')
        sub2.add_argument('--delete-sub', arg_type='+')
        sys.argv = ['test.py', '--clear-all-sub', 'sub', '--delete-sub', 'AAA']
        self.assertIsInstance(c.parse_command(), NameSpace)


if __name__ == '__main__':
    unittest.main()
