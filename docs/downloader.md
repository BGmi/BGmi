# 扩展下载方式

bgmi 的下载方式是用`entry_points`注册，并使用`stevedore`来加载的。

可以通过添加`entry_points`的方式添加下载工具支持。

例子: <bgmi/downloader/>

需要实现[`bgmi.plugin.download:BaseDownloadService`](./bgmi/plugin/download.py)的所有方法。

然后在 setup.py 中指定 entry_points 为`"bgmi.downloader"`

```bash
# setup.py for your package

setup(
    ...,
    entry_points = {
        "bgmi.downloader": ['my-downloader=boo.bar:MyRpcClass'],
    },
    ...,
)
```

```bash
NAME="my-downloader"
bgmi config DOWNLOAD_DELEGATE ${NAME}
```
