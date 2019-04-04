import json

import peewee as pw


class SubtitleField(pw.TextField):
    def python_value(self, value):
        if value:
            return [x.strip() for x in value.split(',')]
        return []

    def db_value(self, value):
        if value:
            return ', '.join(value)
        return ''


class BangumiNamesField(SubtitleField):
    def python_value(self, value):
        if value:
            return {x.strip() for x in value.split(',')}
        return set()

    def db_value(self, value):
        if value:
            if isinstance(value, str):
                return value
            return ', '.join(value)
        return ''


class JSONField(pw.TextField):
    # field_type = ''

    def python_value(self, value):
        if value is not None:
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return value

    def db_value(self, value):
        if value is not None:
            return json.dumps(value)
