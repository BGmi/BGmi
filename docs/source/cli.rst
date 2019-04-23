Command Line Interface
======================


简介
----

bgmi的命令由一系列 ``action`` 组成.

.. code-block:: bash

    bgmi ${action} --args

..
    .. argparse::
       :module: bgmi.main
       :func: get_arg_parser
       :prog: bgmi


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

    bgmi add [--episode episode] [--not-ignore] name [name ...]

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

    bgmi filter [-h] [--subtitle subtitle] [--include include]
                     [--exclude exclude] [--regex regex]
                     [--data-source data_source]
                     name


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


list
----

输出所有订阅的番剧
