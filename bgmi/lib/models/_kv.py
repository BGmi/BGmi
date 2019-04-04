import functools

import peewee as pw
from playhouse import kv

from ._db import db


def create_kv_storage():
    instance = kv.KeyValue(database=db)
    instance.create_model().create_table()
    return instance


# @_kv_storage_decorator
def get_kv_storage() -> kv.KeyValue:
    return kv.KeyValue(database=db)
