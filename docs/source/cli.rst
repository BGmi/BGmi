Command Line Interface
======================

简介
----

Cli 基于 `click <https://click.palletsprojects.com/en/7.x/>`_, 由 ``click`` 提供bash和zsh的自动补全。

激活自动补全：

添加到.bashrc中

.. code-block:: bash

    eval "$(_BGMI_COMPLETE=source bgmi)"

.. code-block:: zsh

    eval "$(_BGMI_COMPLETE=source_zsh bgmi)"


bgmi的命令由一系列 ``action`` 组成.

.. code-block:: bash

    bgmi ${action} --args

Cal
---

打印番剧列表

.. program:: cal

.. option:: --today

    只输入本日番剧

.. option:: -f, --force-update

    强制更新

.. option:: --download-cover

    下载所有的封面

.. option:: --no-save

    在强制更新番剧的时候不保存的数据库中.

Add
---

订阅番剧


.. code-block:: bash

    bgmi add name [name ...] [--episode episode] [--not-ignore]

.. program:: add

.. option:: name

    需要添加的番剧列表, 可以同时添加多个.

.. option:: --episode episode

    添加的同时会标记集数, 如果没有此选项, 会自动标记为最近的一集.

.. option:: --not-ignore

    不忽略超过三个月的旧种子.

Delete
------

删除番剧


.. code-block:: bash

    bgmi delete --name name [name ...]

.. program:: delete

.. option:: --name name [name ...]

    要删除的番剧名

.. option:: --clear-all

    删除所有订阅的番剧. ``--name`` 将会被忽略.
    需要确认.

.. option:: --batch

    如果使用 :option:`bgmi delete --clear-all <delete --clear-all>` 不需要再确认



Filter
------

针对某一个番剧设置过滤关键词

.. code-block:: bash

    bgmi filter name [--subtitle subtitle] [--include include]
                 [--exclude exclude] [--regex regex]
                 [--data-source data_source]



.. program:: filter

.. option:: name

    要修改设置的番剧名


.. option:: --subtitle subtitle

    订阅的字幕组, 如果要订阅多个字幕组, 以 ``,`` 分割

.. option:: --include include

    只下载包含这些关键词的番剧, 多个关键词以 ``,`` 分割

.. option:: --exclude exclude

    排除的关键词, 多个关键词以 ``,`` 分割

.. option:: --regex regex

    正则匹配关键词, 会作用在整个标题上,比如 ``.*720p.*`` 跟 ``--include 720p`` 效果相同

.. option:: --data-source data_source

    从哪些数据源下载, 为空的话会从所有的数据源下载


Update
-------

.. code-block:: bash

    bgmi update [BANGUMI_NAMES ...] [-d/--download] [--not-ignore]

.. program:: update

.. option:: BANGUMI_NAMES

    要更新的番剧名，留空则更新全部订阅番剧

.. option:: -d --download

    是否同时下载番剧


.. warning::

    与2.x版本不同，不能在参数后面指定要更新的集数 :issue:`pallets/click#484`

.. option:: --not-ignore

    是否忽略三个月之前发布的旧种子


list
----

输出所有订阅的番剧
