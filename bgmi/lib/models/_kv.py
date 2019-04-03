import functools

import peewee as pw
from playhouse import kv

from ._db import db


def _kv_storage_decorator(func):
    try:
        kv_instance = [
            func(),
        ]
    except pw.OperationalError:
        kv_instance = []

    @functools.wraps(func)
    def wrapper():
        if not kv_instance:
            kv_instance.append(func())
        return kv_instance[0]

    return wrapper


@_kv_storage_decorator
def get_kv_storage() -> kv.KeyValue:
    kv_instance = kv.KeyValue(database=db)
    return kv_instance
