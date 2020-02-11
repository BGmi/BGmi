=============
HTTP API Spec
=============


Index
-----

index
~~~~~

``/api/index`` 中为更新中的番剧. ``cover`` 字段为完整的path
``player.$episode.path`` 字段需要跟 ``/bangumi`` 进行拼接,才是最终的path.

比如 ``海贼王`` 第一集的实际视频文件地址应该是 ``/bangumi/海贼王/1/1.mp4``


.. warning::
    ``player`` 中的 ``path`` 以后会修改为完整的path, 不再需要客户端手动拼接

..  http:example:: curl wget httpie python-requests

    GET /api/index HTTP/1.1
    Host: localhost:8888
    Accept: application/json


    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "version": "3.0.0a0",
      "latest_version": null,
      "frontend_version": "1.1.x",
      "status": "success",
      "lang": "zh_cn",
      "danmaku_api": "",
      "data": [
        {
          "bangumi_name": "名侦探柯南",
          "cover": "/bangumi/cover/http/lain.bgm.tv/pic/cover/l/01/88/899_Q3F3X.jpg",
          "episode": 0,
          "status": 1,
          "player": {}
          "updated_time": 0,
          "update_time": "Sat",
        },
        {
          "update_time": "Sun",
          "cover": "/bangumi/cover/http/lain.bgm.tv/pic/cover/l/92/97/975_YKuWd.jpg",
          "updated_time": 233,
          "status": 1,
          "bangumi_name": "海贼王",
          "player": {
            "1": {
              "path": "/海贼王/1/1.mp4"
            }
          }
        },
        {
          "cover": "/bangumi/cover/lain.bgm.tv/pic/cover/l/da/bf/83124_t8vg0.jpg",
          "bangumi_name": "妖怪手表",
          "episode": 0,
          "status": 1,
          "player": {}
          "update_time": "Fri",
          "updated_time": 0,
        }
      ]
    }

Old
~~~

``/api/old`` 中为旧番, 即已经完结的番剧.

..  http:example:: curl wget httpie python-requests

    GET /api/old HTTP/1.1
    Host: localhost:8888
    Accept: application/json


    HTTP/1.1 200 OK
    Content-Type: application/json

    Response has same schema with ``/api/index``


Resource
--------

rss
~~~

订阅番剧的Rss feed,可以导出给uTorrent等支持rss的客户端使用.

具体的下载地址为资源站提供的磁链.

..  http:example:: curl wget httpie python-requests

    GET /resource/feed.xml HTTP/1.1
    Host: localhost:8888

iCalendar
~~~~~~~~~

iPhone支持的ics格式日历,包含了番剧的更新时间.

..  http:example:: curl wget httpie python-requests

    GET /resource/calendar.ics HTTP/1.1
    Host: localhost:8888



Admin
-----

用于部分代替cli管理番剧的http api

.. module:: bgmi.front.admin

.. py:data:: API_MAP_GET

    定义了使用get方法访问的几个api

.. py:data:: API_MAP_POST

    定义了使用get方法访问的几个api

.. py:data:: NO_AUTH_ACTION

    一个列表,其中对应的controllers不需要认证即可使用
    现在为 ``auth`` 和 ``cal``


cal
~~~

获取全部的番剧列表,包括番剧和额外添加的scripts

根据 ``status`` 来判断是否已经订阅.

..  http:example:: curl wget httpie python-requests

    GET /api/cal HTTP/1.1
    Host: localhost:8888
    Accept: application/json


    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "version": "3.0.0a0",
      "latest_version": null,
      "frontend_version": "1.1.x",
      "status": "success",
      "lang": "zh_cn",
      "danmaku_api": "",
      "data": {
        "wed": [
          {
            "status": null,
            "episode": null,
            "id": 22,
            "name": "猫猫日本史 第四季",
            "cover": "http/lain.bgm.tv/pic/cover/l/1d/b1/279471_VB4qr.jpg",
            "subject_id": 279471,
            "update_time": "Wed",
            "has_data_source": 1
          }
        ],
        "thu": [
          {
            "status": null,
            "episode": null,
            "id": 28,
            "name": "偶像活动Friends～闪耀的宝石～",
            "cover": "http/lain.bgm.tv/pic/cover/l/e2/ed/272921_Wkee1.jpg",
            "subject_id": 272921,
            "update_time": "Thu",
            "has_data_source": 1
          }
        ],
        "fri": [
          {
            "status": 1,
            "episode": 0,
            "id": 30,
            "name": "妖怪手表",
            "cover": "http/lain.bgm.tv/pic/cover/l/da/bf/83124_t8vg0.jpg",
            "subject_id": 83124,
            "update_time": "Fri",
            "has_data_source": 1
          }
        ],
        "sat": [
          {
            "status": 2,
            "episode": 935,
            "id": 41,
            "name": "名侦探柯南",
            "cover": "http/lain.bgm.tv/pic/cover/l/01/88/899_Q3F3X.jpg",
            "subject_id": 899,
            "update_time": "Sat",
            "has_data_source": 1
          }
        ],
        "sun": [
          {
            "status": 1,
            "episode": 877,
            "id": 49,
            "name": "海贼王",
            "cover": "http/lain.bgm.tv/pic/cover/l/92/97/975_YKuWd.jpg",
            "subject_id": 975,
            "update_time": "Sun",
            "has_data_source": 1
          },
          {
            "status": null,
            "episode": null,
            "id": 63,
            "name": "Fairy gone フェアリーゴーン",
            "cover": "http/lain.bgm.tv/pic/cover/l/39/23/272475_2w799.jpg",
            "subject_id": 272475,
            "update_time": "Sun",
            "has_data_source": 1
          },
          {
            "status": null,
            "episode": null,
            "id": 65,
            "name": "荒野的寿飞行队 外传 大空的晴风飞行队",
            "cover": "http/lain.bgm.tv/pic/cover/l/ed/6c/279048_10u3T.jpg",
            "subject_id": 279048,
            "update_time": "Sun",
            "has_data_source": 1
          }
        ],
        "mon": [
          {
            "bangumi_name": "生活大爆炸S12",
            "cover": "http/tu.jstucdn.com/ftp/2018/1023/b_863118231740caaf847a935ddab3fd5d.jpg",
            "update_time": "Mon",
            "name": "生活大爆炸S12",
            "status": 2,
            "updated_time": 1555178097,
            "subtitle_group": "",
            "episode": 1218,
            "is_script": true,
            "has_data_source": 1
          }
        ],
        "tue": [
          {
            "bangumi_name": "少年谢尔顿S2",
            "cover": "http/tu.jstucdn.com/ftp/2018/1023/b_69c10508586e2509a1a94f448c2e12e3.jpg",
            "update_time": "Tue",
            "name": "少年谢尔顿S2",
            "status": 2,
            "updated_time": 1555178097,
            "subtitle_group": "",
            "episode": 218,
            "is_script": true,
            "has_data_source": 1
          }
        ]
      }
    }

.. note::

    ``status`` 参照

    .. module:: bgmi.lib.models._tables

    .. class:: Followed.STATUS

        Followed.STATUS
