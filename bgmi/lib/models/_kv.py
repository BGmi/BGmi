import functools

import peewee as pw
from playhouse import kv

from ._db import db


class KV(kv.KeyValue):
    def __setitem__(self, expr, value):
        if not isinstance(value, str):
            raise ValueError("kv's item must be str")
        super().__setitem__(expr, value)


def create_kv_storage():
    instance = KV(database=db, value_field=pw.TextField())
    instance.create_model().create_table()
    return instance


def _kv_storage_decorator(func):
    reference = []

    @functools.wraps(func)
    def wrapped():
        if not reference:
            reference.append(func())
        return reference[0]

    return wrapped


@_kv_storage_decorator
def get_kv_storage() -> kv.KeyValue:
    return KV(database=db, value_field=pw.TextField())
