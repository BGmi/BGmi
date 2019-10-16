import peewee as pw
from playhouse.db_url import connect

import bgmi.config

db = connect(bgmi.config.DB_URL)

# T = TypeVar('T', bound=pw.Model)


class NeoDB(pw.Model):
    class Meta:
        database = db

    @classmethod
    def has_status(cls, status):
        print(status in list(map(int, cls.STATUS)))

    @classmethod
    def fuzzy_get(cls, **filters):
        q = []
        for key, value in filters.items():
            q.append(getattr(cls, key).contains(value))
        o = list(cls.select().where(*q))
        if not o:
            raise cls.DoesNotExist
        return o[0]


class FuzzyMixIn:
    pass
