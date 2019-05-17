================================
Welcome to BGmi's documentation!
================================

Update Log
==========
+ 抓取到多个种子的时候进行排序 :issue:`143`
+ 同时从多个数据源抓取数据. :issue:`109`
+ 不再支持python2 :issue:`104`

Feature
=======
+ 支持多个数据源: `bangumi_moe <https://bangumi.moe>`_, `mikan_project <https://mikanani.me>`_ or `dmhy <https://share.dmhy.org/>`_
+ 使用aria2, transmission or deluge下载番剧
+ 通过WebUI来观看下载的番剧, 或者管理下载
+ Play bangumi online with danmaku
+ RSS feed 和 icalendar 格式的日历
+ BGmi Script: 自定义番剧解析器
+ 关键词, 字幕组或者正则过滤器
+ Windows和Linux系统支持

.. toctree::

    config
    cli
    controllers
    http_api
    plugins
    data_source_base
    development
