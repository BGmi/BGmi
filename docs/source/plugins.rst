=============
BGmi Plugins
=============


Name Space
----------

``BGmi`` 使用 `stevedore <https://github.com/openstack/stevedore>`_ 来加载可用的数据源和下载工具

添加数据源
~~~~~~~~~~

.. note::

    用这个办法添加的数据源只能是动画番剧,而不能是美剧.

自己编写一个python package，在setup.cfg 或者setup.py中定义 ``entry_points``。
与 ``BGmi`` 安装到同一个虚拟环境中让 ``BGmi`` 可以搜索到你的插件

比如 ``BGmi`` 的 ``setup.cfg``:

.. code-block:: ini

    [options.entry_points]
    bgmi.data_source.provider =
      bangumi_moe = bgmi.website.bangumi_moe:BangumiMoe
      mikan_project = bgmi.website.mikan:Mikanani
      dmhy = bgmi.website.share_dmhy:DmhySource

.. warning::

    ``bgmi.downloader.delegate`` 目前并不能被扩展, 只能使用bgmi提供的三种下载方法之一

``BGmi`` 会使用 ``stevodore`` 的 ``ExtensionManager`` 从
``bgmi.data_source.provider`` 命名空间来加载所有可用的数据源, 并在加载时实例化.

数据源应该继承 :py:class:`bgmi.website.base.BaseWebsite`,并且实现所有的 ``abstractmethod``:

.. py:currentmodule:: bgmi.website.base

+ :py:func:`BaseWebsite.fetch_bangumi_calendar_and_subtitle_group`
+ :py:func:`BaseWebsite.fetch_episode_of_bangumi`
+ :py:func:`BaseWebsite.search_by_keyword`

.. note::

    如果网站没有提供种子对应的集数, 你可以使用 :py:func:`BaseWebsite.parse_episode` 来解析标题得到对应的集数.
