import functools
from os import path

import peewee as pw
from playhouse.kv import KeyValue

from bgmi import config


def create_kv_storage():
    return KeyValue(database=pw.SqliteDatabase(path.join(config.BGMI_PATH, 'kv.db')))


def _kv_storage_decorator(func):
    reference = []

    @functools.wraps(func)
    def wrapped():
        if not reference:
            reference.append(func())
        return reference[0]

    return wrapped


@_kv_storage_decorator
def get_kv_storage():
    return create_kv_storage()
