BGmi
====
BGmi is a cli tool for subscribed bangumi.

|travis| 

====
TODO
====
+ Download Bangumi by file format, file size
+ Email remind when the bangumi been downloaded

=======
Feature
=======
+ Subscribe/Unsubscribe bangumi
+ Bangumi-updating schedule
+ Bangumi episode informatdon
+ HTTP Server for RSS feed (for uTorrent, etc.)
+ Download bangumi by subtitle group

.. image:: https://raw.githubusercontent.com/RicterZ/BGmi/master/images/1.png
    :alt: BGmi
    :align: center
.. image:: https://raw.githubusercontent.com/RicterZ/BGmi/master/images/2.png
    :alt: BGmi
    :align: center

============
Installation
============
For **Mac OS X / Linux**:

.. code-block:: bash

    git clone https://github.com/RicterZ/BGmi
    cd BGmi
    python setup.py install

Or use pip:

.. code-block:: bash

    pip install bgmi

For **Windows**: BGmi does not support Windows now.  

=====
Usage
=====
Show bangumi calendar of this week:

.. code-block:: bash

    bgmi cal all


Subscribe bangumi:

.. code-block:: bash

    bgmi add "Re：從零開始的異世界生活" "暗殺教室Ⅱ" "線上遊戲的老婆不可能是女生？" "在下坂本，有何貴幹？" "JoJo的奇妙冒險 不滅鑽石"


Unsubscribe bangumi:

.. code-block:: bash

    bgmi delete --name "暗殺教室Ⅱ"


Update bangumi calendar and episode, and write to download.xml:

.. code-block:: bash

    bgmi update --download


Start a HTTP Server for download.xml:

.. code-block:: bash

    bgmi http --port 12345


Set bangumi filter and fetch entries by subtitle group:

.. code-block:: bash

    bgmi filter "線上遊戲的老婆不可能是女生？" "KNA,惡魔島"
    bgmi fetch "線上遊戲的老婆不可能是女生？"

Install `xunlei-lixian <https://github.com/iambus/xunlei-lixian/>`_:

.. code-block:: bash

    bgmi install



=======
License
=======
MIT

.. |travis| image:: https://travis-ci.org/RicterZ/BGmi.svg?branch=master
   :target: https://travis-ci.org/RicterZ/BGmi

