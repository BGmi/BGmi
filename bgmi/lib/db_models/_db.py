import peewee as pw
from playhouse import db_url

from bgmi.config import advanced_config_obj, config_obj
from bgmi.models.config import AdvancedConfig, Config


def get_db(config: Config, advanced_config: AdvancedConfig):
    if advanced_config.DB_URL:
        db = db_url.connect(advanced_config.DB_URL)
    else:
        db = pw.SqliteDatabase(config.DB_PATH)
    return db


db = get_db(config_obj, advanced_config_obj)


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
