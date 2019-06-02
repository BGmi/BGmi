"""Peewee migrations -- 001_init.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.python(func, *args, **kwargs)        # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import peewee as pw

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""

    @migrator.create_model
    class Bangumi(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255, unique=True)
        cover = pw.CharField(default='', max_length=255)
        status = pw.IntegerField(default=0)
        subject_id = pw.IntegerField(null=True)
        update_time = pw.FixedCharField()
        has_data_source = pw.IntegerField(default=0)

        class Meta:
            table_name = 'bangumi'

    @migrator.create_model
    class BangumiItem(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255)
        cover = pw.CharField(max_length=255)
        status = pw.IntegerField()
        update_time = pw.FixedCharField()
        subtitle_group = pw.TextField()
        keyword = pw.CharField(max_length=255)
        data_source = pw.FixedCharField()
        bangumi_id = pw.IntegerField(default=0)

        class Meta:
            table_name = 'bangumi_item'
            indexes = [(('keyword', 'data_source'), True)]

    @migrator.create_model
    class Download(pw.Model):
        id = pw.AutoField()
        name = pw.CharField(max_length=255)
        title = pw.CharField(max_length=255)
        episode = pw.IntegerField(default=0)
        download = pw.CharField(max_length=255)
        status = pw.IntegerField(default=0)

        class Meta:
            table_name = 'download'

    @migrator.create_model
    class Followed(pw.Model):
        bangumi_id = pw.IntegerField(primary_key=True)
        episode = pw.IntegerField(default=0, null=True)
        status = pw.IntegerField(null=True)
        updated_time = pw.IntegerField(null=True)
        data_source = pw.FixedCharField(default='')
        subtitle = pw.CharField(default='', max_length=255)
        include = pw.CharField(default='', max_length=255)
        exclude = pw.CharField(default='', max_length=255)
        regex = pw.CharField(default='', max_length=255)

        class Meta:
            table_name = 'followed'

    @migrator.create_model
    class Scripts(pw.Model):
        id = pw.AutoField()
        bangumi_name = pw.CharField(max_length=255, unique=True)
        episode = pw.IntegerField(default=0)
        status = pw.IntegerField(default=0)
        updated_time = pw.IntegerField(default=0)

        class Meta:
            table_name = 'scripts'

    @migrator.create_model
    class Subtitle(pw.Model):
        id = pw.CharField(max_length=255)
        name = pw.CharField(max_length=255)
        data_source = pw.CharField(max_length=30)

        class Meta:
            table_name = 'subtitle'
            indexes = [(('id', 'data_source'), True)]


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""

    migrator.remove_model('subtitle')

    migrator.remove_model('scripts')

    migrator.remove_model('followed')

    migrator.remove_model('download')

    migrator.remove_model('bangumi_item')

    migrator.remove_model('bangumi')
