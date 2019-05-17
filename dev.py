import argparse

from peewee_migrate import Router

from bgmi.lib.models import db


def get_parser():
    r = argparse.ArgumentParser()
    sub_parser = r.add_subparsers(dest='action')
    sub_parser.add_parser('migrate', help='create a migration').add_argument('name')
    return r


def main():
    parser = get_parser()
    ret = parser.parse_args()
    if ret.action == migrate.__qualname__:
        migrate(ret.name)


def migrate(name):
    router = Router(db, migrate_dir='bgmi/lib/models/migrations', ignore=['neodb'])

    router.create(name, auto=True)


if __name__ == '__main__':
    main()
