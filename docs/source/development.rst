====
开发
====

1. 参照 `contributing.md <https://github.com/BGmi/BGmi/blob/dev/.github/contributing.md>`_

2. 如果修改了表结构，需要使用 ``python dev.py migrate ${migration_name}`` 来生成migration。
然后修改生成的migration文件，使其符合代码规范

.. warning::

    使用 ``autoflake`` 自动移除未用到的 ``import`` 后，由于 :issue:`myint/autoflake/#52` 会生成一段无意义的代码，请注意删除。

    ``peewee_migrate`` 对字段的default值处理有bug
    如果前一个migration中的 ``constraints=[SQL("DEFAULT 0")]`` 没有被修改为 ``default=0`` 的形式，
    ``peewee-migrate`` 会认为此字段值添加了默认值，请手动修改。

    所有的 ``primary_key=True`` 的字段不能添加 ``unique=True``，
    否则会生成一个试图 ``drop_index`` 的migration。(primary_key本身就是unique的，无此必要)

3. 请确认travis-ci和circleci上测试通过。
