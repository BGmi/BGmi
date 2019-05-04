配置BGmi
========

设定环境变量
-----------

.. py:data:: BGMI_PATH

   所有持久化的数据, 比如配置文件 ``bgmi.cfg`` 数据库 ``bangumi.db``.

.. py:data:: BGMI_LOG

    日志等级, 可以设置为 ``debug`` , ``info`` (默认), ``warning``, ``error`` .
    日志文件会保存在 :py:data:`TMP_PATH` ``/bgmi.log``

.. py:data:: DEBUG

    有时候 ``BGmi`` 会忽略某些错误, 比如 ``search`` 中的错误,
    如果你无法正常的使用某些功能, 又不能确定哪里出了错误, 不为空时会抛出一些原本不会抛出的错误.

.. py:data:: DEV

    输出warning

设置任意writable的config
~~~~~~~~~~~~~~~~~~~~~~~~

所有当前可写的配置项都可以通过环境变量来设置。方法为在对应配置项的名字前加 ``BGMI_``。
例如，设置环境变量 ``BGMI_LOG_LEVEL`` 的值为 ``warning``。
这会把 ``bgmi.config.LOG_LEVEL`` 的值设置为 ``warning``，并且覆盖配置文件中的设置。

方便在docker中设置bgmi。




通过命令或者直接修改配置文件
-------------------------

显示当前设置

.. code-block:: bash

    bgmi config

显示 ``$KEY`` 的当前设置

.. code-block:: bash

    bgmi config $KEY

修改某项设置

.. code-block:: bash

    bgmi config $KEY $VALUE

配置文件位于 :py:data:`${BGMI_PATH}/bgmi.cfg <BGMI_PATH>`

.. py:data:: SAVE_PATH

    番剧保存的文件夹, 默认为 :py:data:`BGMI_PATH`/bangumi ,
    所有的番剧都会保存在这个文件夹内.

.. py:data:: LOG_LEVEL

    日志等级，应该为 ``debug``，``info``，``warning``，``error``

.. py:data:: DOWNLOAD_DELEGATE

    下载工具, 使用 ``aria2-rpc`` ,  ``transmission-rpc`` 或者 ``deluge-rpc``.

.. py:data:: DB_URL

    参照
    `peewee#database-url <https://docs.peewee-orm.com/en/latest/peewee/playhouse.html#database-url>`_,
    默认会使用sqlite

.. py:data:: MAX_PAGE

    当抓取数据源的时候最大的抓取页数

.. py:data:: TMP_PATH

    存放某些临时文件的路径.

.. py:data:: DISABLED_DATA_SOURCE

     禁用的数据源

.. py:data:: ENABLE_GLOBAL_FILTER

    是否启用全局排除关键词

.. py:data:: GLOBAL_FILTER

    全局过滤关键词, 以 ``,`` 分割.

.. py:data:: TORNADO_SERVE_STATIC_FILES

    是否用tornado代理静态文件, 建议使用nginx或者caddy代理静态文件.

.. py:data:: BANGUMI_MOE_URL

    bangumi.moe镜像站链接, 默认为源站链接

.. py:data:: SHARE_DMHY_URL

    动漫花园镜像站链接, 默认为源站链接.

.. py:data:: LANG

    语言设置, 目前还没有实际用处

web相关的设置
-------------


.. py:data:: DANMAKU_API_URL

    dplayer使用的弹幕库后端.

.. py:data:: ADMIN_TOKEN

    前端的管理界面


关键词权重
----------


在同时抓取到多个种子的时候, 会按照相应的权重排序关键词.

添加一个 ``[keyword weight]``, 在其中定义一组键值对. 以关键词做为键, 把权重做为值.

example:

.. code-block:: ini

    [keyword weight]
    720 = 10
    内嵌 = 100
    双语 = 100

如果有三个种子分别标题为 ``720p 简体``, ``1080p 双语`` 和 ``720 内嵌 双语``,
他们最终计算出的权重会是 ``10``, ``100`` 和 ``210`` (``10+100+100``)
第三个种子权重最高, 所以会下载第三个种子.

各种下载方法相关的设置
--------------------

Aria2-rpc
~~~~~~~~~


.. py:data:: ARIA2_RPC_URL

    xml-rpc对应的链接, (非jsonrpc链接).(应该以 ``/rpc`` )

.. py:data:: ARIA2_RPC_TOKEN

    rpc token(如果没有设置secret, 保持默认或者设置为 ``token:``)

Transmission-rpc
~~~~~~~~~~~~~~~~

.. py:data:: TRANSMISSION_RPC_URL

    transmission-rpc host

.. py:data:: TRANSMISSION_RPC_PORT

    transmission-rpc port

.. py:data:: TRANSMISSION_RPC_USERNAME

    transmission-rpc username(保持默认值如果没有使用认证)

.. py:data:: TRANSMISSION_RPC_PASSWORD

    transmission rpc password(保持默认值如果没有使用认证)

Deluge-rpc
~~~~~~~~~~

.. py:data:: DELUGE_RPC_URL

    deluge rpc url

.. py:data:: DELUGE_RPC_PASSWORD

    deluge rpc password
