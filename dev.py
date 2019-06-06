import argparse

from peewee_migrate import Router

from bgmi.lib.db_models import Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle, db


def get_parser():
    r = argparse.ArgumentParser()
    sub_parser = r.add_subparsers(dest='action')
    sub_parser.add_parser('migrate', help='create a migration').add_argument('name')
    sub_parser.add_parser('create_tables', help='create tables manually')
    return r


def create_tables():
    db.create_tables([Bangumi, BangumiItem, Download, Followed, Scripts, Subtitle])


def main():
    parser = get_parser()
    ret = parser.parse_args()
    if ret.action == migrate.__qualname__:
        migrate(ret.name)
    elif ret.action == create_tables.__qualname__:
        create_tables()


def migrate(name):
    router = Router(db, migrate_dir='bgmi/lib/db_models/migrations', ignore=['neodb'])

    router.create(name, auto=True)


if __name__ == '__main__':
    main()
