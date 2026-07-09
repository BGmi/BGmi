# BGmi

BGmi 是一个用来追番的命令行程序。

[![](https://img.shields.io/pypi/v/bgmi.svg)](https://pypi.python.org/pypi/bgmi)
[![Downloads](https://pepy.tech/badge/bgmi/month)](https://pepy.tech/project/bgmi/month)
[![test](https://github.com/BGmi/BGmi/actions/workflows/test.yaml/badge.svg)](https://github.com/BGmi/BGmi/actions/workflows/test.yaml)
[![](https://codecov.io/gh/BGmi/BGmi/branch/master/graph/badge.svg)](https://codecov.io/gh/BGmi/BGmi/branch/master/graph/badge.svg)
[![](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/BGmi/BGmi/blob/master/LICENSE)

## 更新日志

### V5

v5 是一次主要版本更新，重点是更可靠的单集追踪、更适合媒体库的下载整理，以及新的 HTTP/MCP 管理接口。

#### 主要变化

- 改为按单集记录下载状态。单集下载失败时，可用 `seen forget` 重新加入更新队列，不再需要回退整部番剧的进度。
- 新增 `seen mark` / `seen forget`，用于手动添加或移除单集记录。
- 新增 path formatter 和 `postprocess`。启用后，下载中的文件会先进入 `.downloads`，完成后整理为 `SxxExx` 等媒体库常用路径。
- `add` 支持 `--season`、`--episode-offset`、`--display-name`，用于修正季度、总集数偏移和媒体库显示名。
- `bgmi_http` 新增 MCP 接口，供 MCP 客户端管理订阅、过滤器、更新和下载状态。
- `bgmi install` 支持从 GitHub Release 安装新版前端。

#### 不兼容变化

- Python 版本要求提升到 3.11+。
- `mark` 命令由 `seen mark` / `seen forget` 取代。
- `update` 现在默认执行下载，不再使用旧的 `--download` 参数。
- v4 数据库需要在升级后运行 `bgmi upgrade` 完成迁移。

---

### v4

- 添加 `proxy` 设置。
- 新 Web UI。
- 将配置项 `transmission.rpc_url` 重命名为 `transmission.rpc_host`。
- 修复 Transmission 配置的默认值。

### v3

- 新增配置项 `global_include_keywords`，用于设置全局包含关键词。
- 新增配置项 `save_path_map`，用于设置不同动画的下载路径。
- 使用 [TOML](https://github.com/toml-lang/toml) 作为配置文件。
- 不再支持 Python 3.7 及以下版本。
- 支持[扩展下载方式](./docs/downloader.md)。
- 移除迅雷离线。
- 支持 [qbittorrent-webapi](https://www.qbittorrent.org/)。
- Transmission RPC 认证设置。
- 支持 [deluge-rpc](https://www.deluge-torrent.org/)。
- 使用最大和最小集数筛选搜索结果。

## 特性

- 多个数据源可选：[bangumi_moe](https://bangumi.moe)、[mikan_project](https://mikanani.me) 或者 [dmhy](https://share.dmhy.org/)。
- 使用 aria2、transmission、qbittorrent 或者 deluge 来下载你的番剧。
- 提供一个管理和观看订阅番剧的前端。
- 弹幕支持。
- 提供移动设备支持的 ICS 格式日历。
- Bangumi Script：添加自己的番剧解析器。
- 番剧放送列表和剧集信息。
- 下载番剧时的过滤器（支持关键词、字幕组和正则）。
- 多平台支持：Windows、macOS 以及 Linux。

![](./images/bgmi_cli.png?raw=true)
![](https://github.com/BGmi/BGmi-frontend/raw/master/.github/images/example.png)
![](https://github.com/BGmi/BGmi-frontend/raw/master/.github/images/example2.png)

## 安装

使用 [pipx](https://pypa.github.io/pipx/) 安装（推荐）：

```bash
pipx install bgmi
```

安装 v5 预发布版本：

```bash
pipx install "bgmi==5.0.0a4"
```

### 使用 pip 安装稳定版本

```bash
pip install bgmi
```

使用 pip 安装 v5 预发布版本：

```bash
pip install "bgmi==5.0.0a4"
```

### 从源码安装（不推荐）

```bash
git clone https://github.com/BGmi/BGmi
cd BGmi
git checkout master
python -m pip install -U pip
pip install .
```

### 初始化 BGmi

```bash
bgmi install
```

## 升级

### pipx 安装

```bash
pipx upgrade bgmi
bgmi upgrade
```

### pip 安装

```bash
pip install bgmi -U
bgmi upgrade
```

升级后请确保运行 `bgmi upgrade`。

## 使用 Docker

见 [BGmi/bgmi-docker-all-in-one](https://github.com/BGmi/bgmi-docker-all-in-one)。

## 使用

查看可用的命令：

```bash
bgmi --help
```

**`--help` 选项同样适用于所有子命令，README 仅介绍基础用法。**

## 配置 BGmi

BGmi 提供两种方式配置运行参数：配置文件与环境变量。

### 配置文件

BGmi 的配置文件位于 `${BGMI_PATH}/config.toml`。在未设置 `BGMI_PATH` 环境变量时，`${BGMI_PATH}` 默认为 `~/.bgmi/`。

查看当前 BGmi 设置：

```bash
bgmi config print
```

```toml
data_source = "bangumi_moe" # 数据源
download_delegate = "aria2-rpc" # 番剧下载工具（aria2-rpc、transmission-rpc、deluge-rpc、qbittorrent-webapi）
tmp_path = "tmp/tmp" # 临时目录
log_path = "tmp/log" # 日志目录
save_path = "tmp/bangumi" # 下载番剧保存地址
enable_path_formatter = false # 启用后，完成下载会整理为 path_formatter 指定的路径
path_formatter = "{name}/S{season:02d}/S{season:02d}E{episode:02d}.{suffix}" # 媒体库文件路径格式
max_path = 3 # 抓取数据时每个番剧最大抓取页数
bangumi_moe_url = "https://bangumi.moe"
share_dmhy_url = "https://share.dmhy.org"
mikan_username = "" # 蜜柑计划的用户名
mikan_password = "" # 蜜柑计划的密码
enable_global_filters = true
global_filters = [
  "Leopard-Raws",
  "hevc",
  "x265",
  "c-a Raws",
  "U3-Web",
]

proxy = '' # HTTP 代理，例如：http://127.0.0.1:1080

[save_path_map] # 针对每部番剧设置下载路径
'致不灭的你 第二季' = '/home/trim21/downloads/bangumi/致不灭的你/s2/' # 绝对路径可能导致 web-ui 无法正确显示视频文件
'致不灭的你 第三季' = './致不灭的你/s3/' # 以 save_path 为基础路径的相对路径

[http]
admin_token = "dYMj-Z4bDRoQfd3x" # Web UI 的密码
danmaku_api_url = ""
serve_static_files = false

[aria2]
rpc_url = "http://localhost:6800/rpc" # aria2c RPC URL（不是 jsonrpc URL）
rpc_token = "token:" # aria2c RPC token（如果没有设置 token，留空或者设置为 `token:`）

[transmission]
rpc_host = "127.0.0.1"
rpc_port = 9091
rpc_username = "your_username"
rpc_password = "your_password"
rpc_path = "/transmission/rpc" # Transmission HTTP RPC 的请求路径

[qbittorrent]
rpc_host = "127.0.0.1"
rpc_port = 8080
rpc_username = "admin"
rpc_password = "adminadmin"
category = ""

[deluge]
rpc_url = "http://127.0.0.1:8112/json"
rpc_password = "deluge"
```

### 环境变量

当 BGmi 的配置文件还未初始化时，各项运行参数可由环境变量进行配置。

环境变量以 `BGMI_` 开头，全大写命名，各级配置以 `_` 进行分割，例如：

```
BGMI_DATA_SOURCE=bangumi_moe    # 对应配置文件中的 data_source = "bangumi_moe"
BGMI_HTTP_ADMIN_TOKEN=dYMj-Z4bDRoQfd3x    # 对应配置文件 [http] 下的 admin_token
```

环境变量**暂不支持**配置以下项目：

```
enable_global_include_keywords
enable_global_filters
global_include_keywords
global_filters
[save_path_map]
```

注：当配置文件生成完毕后，运行配置将会以配置文件为准。环境变量仅用于生成第一份配置文件。

## 修改配置

使用 `bgmi config set ...keys --value '...'` 命令可以修改配置。例如：

```shell
bgmi config set http admin_token --value 'my super secret token'
```

或者：

```shell
bgmi config set max_path --value '3'
```

不能用来修改复杂配置（如 `global_filters`），请手动修改配置文件。

## 支持的数据源

- [bangumi_moe](https://bangumi.moe)（默认）
- [mikan_project](https://mikanani.me)
- [dmhy](https://share.dmhy.org/)

### 更换数据源

**更换数据源会清空番剧数据库，但是 bgmi script 不受影响。** 之前下载的视频文件不会删除，但不会在前端显示。

**如果更换的源为 `mikan_project`，请先配置 `MIKAN_USERNAME` 和 `MIKAN_PASSWORD`。** 其它源不受影响。

```bash
bgmi source mikan_project
```

### 设置下载方式

修改配置文件中对应的配置项：

```toml
download_delegate = "aria2-rpc" # 下载方式
```

内置可用的选项包括 `aria2-rpc`、`transmission-rpc`、`qbittorrent-webapi` 以及 `deluge-rpc`。

## 订阅管理

### 查看目前正在更新的新番

```bash
bgmi cal
```

### 订阅番剧

```bash
bgmi add "进击的巨人 第三季" "刃牙" "哆啦A梦"
bgmi add "高分少女"
```

默认会从第 1 集开始下载。可以用 `--episode` 标记已经下载过的集数，比如
`--episode 12` 表示从第 13 集开始追；用 `--latest` 可以把当前已经发布的集数都标记为已下载。

添加番剧的同时设置下载路径：

```bash
bgmi add "高分少女" --save-path './高分少女/S1/'
```

设置／修改番剧的季度号：

```bash
bgmi add "爱书的下克上 第4季" --season 1
```

`--season` 对已订阅的番剧同样有效，会直接更新季度号。

### 退订

```bash
bgmi delete "Re:CREATORS"
```

### 更新番剧列表并下载

```bash
bgmi update
bgmi update "从零开始的魔法书"
```

### 下载目录格式

默认情况下，BGmi 仍会把每集下载到 `${save_path}/{番剧名}/{集数}/`。

设置 `enable_path_formatter = true` 后，下载器会先把任务保存到 `${save_path}/.downloads/{任务 ID}/`。任务完成后，`bgmi update` 会自动执行 `postprocess`，也可以手动运行 `bgmi postprocess`，将文件移动到 `path_formatter` 指定的位置。

默认格式为：

```toml
path_formatter = "{name}/S{season:02d}/S{season:02d}E{episode:02d}.{suffix}"
```

### 管理已下载集数

v5 会自动记录所有已下载的集数。如果某集下载失败需要重新下载，使用 `seen forget` 移除该集的记录，然后重新 `update`。如果你已经手动处理了某集，也可以用 `seen mark` 将它加入已下载记录：

```bash
bgmi seen forget "Re:CREATORS" 5
bgmi update "Re:CREATORS"
bgmi seen mark "Re:CREATORS" 6
```

## 过滤器

设置筛选条件：

```bash
bgmi list
bgmi fetch "Re:CREATORS"
# include 和 exclude 会忽略大小写。`720p` 和 `720P` 的效果是相同的
bgmi filter "Re:CREATORS" --subtitle "DHR動研字幕組,豌豆字幕组" --include 720P --exclude BIG5
bgmi fetch "Re:CREATORS"
# 删除 subtitle、include 和 exclude，添加正则匹配
bgmi filter "Re:CREATORS" --subtitle "" --include "" --exclude "" --regex "..."
bgmi filter "Re:CREATORS" --regex "(DHR動研字幕組|豌豆字幕组).*(720P)"
bgmi fetch "Re:CREATORS"
```

### 全局过滤关键词

#### 包含

默认不启用全局包含关键词，你可以设置 `enable_global_include_keywords = true` 启用此功能：

```toml
enable_global_include_keywords = true
global_include_keywords = ['1080']
```

#### 排除

有一些默认定义的全局过滤关键词，默认会排除标题包含以下关键词的种子。可以使用 `enable_global_filters = false` 禁止过滤全局关键词：

```toml
enable_global_filters = true
global_filters = [
  "Leopard-Raws",
  "hevc",
  "x265",
  "c-a Raws",
  "U3-Web",
]
```

最后使用 `bgmi fetch` 来查看筛选的结果。

## 搜索

搜索番剧并下载：

```bash
bgmi search '为美好的世界献上祝福！' --regex-filter '.*动漫国字幕组.*为美好的世界献上祝福！].*720P.*'
```

使用 `--min-episode` 和 `--max-episode` 来根据集数筛选下载结果：

```bash
bgmi search 海贼王 --min-episode 800 --max-episode 820
bgmi search 海贼王 --min-episode 800 --max-episode 820 --download
```

`bgmi search` 命令默认不会显示重复的集数。如果要显示重复的集数来方便过滤，在命令后加上 `--dupe` 来显示全部搜索结果。

## 使用 bgmi_http

1. 先下载所有更新中番剧的封面：

```bash
bgmi cal --cover
```

2. 根据你是否使用 nginx，设置 `serve_static_files`（使用 nginx 的情况下使用默认设置 `false`，不使用的情况下设置为 `true`）。

3. 下载前端的静态文件（你可能在安装的时候已经下载过了）：

```bash
bgmi install
```

4. 在 `8888` 端口启动 BGmi HTTP 服务器：

```bash
bgmi_http --port=8888 --address=0.0.0.0
```

### 在 Windows 上使用 bgmi_http

参照上面启动服务器，然后访问 [http://localhost:8888/](http://localhost:8888/)。

### 在 *nix 上使用 bgmi_http

可以让 BGmi 帮助你生成对应的 nginx 配置文件：

```bash
bgmi gen nginx.conf --server-name bgmi.whatever.com
```

你也可以手动写一份 nginx 配置来满足更多需求（比如启用 HTTPS）。以下是一份示例：

```nginx
server {
    listen 80;
    server_name bgmi;

    autoindex on;
    charset utf-8;

    location /bangumi {
        # ~/.bgmi/bangumi
        # alias 到你的 SAVE_PATH，注意以 / 结尾
        alias /path/to/bangumi/;
    }

    location /api {
        proxy_pass http://127.0.0.1:8888;
    }

    location /resource {
        proxy_pass http://127.0.0.1:8888;
    }

    location / {
        # alias 到你的 BGMI_PATH/front_static/，注意以 / 结尾
        alias /path/to/front_static/;
    }
}
```

macOS launchctl service controller 参照 [issue #77](https://github.com/BGmi/BGmi/pull/77) 自行设置。

[me.ricterz.bgmi.plist](https://github.com/BGmi/BGmi/blob/master/bgmi/others/me.ricterz.bgmi.plist)

## 弹幕支持

BGmi 使用 [`DPlayer`](https://github.com/DIYgod/DPlayer) 做为前端播放器。

如果你想要添加弹幕支持，在 [DPlayer#related-projects](https://github.com/DIYgod/DPlayer#related-projects) 选择一个后端自行搭建，或者使用 DPlayer 提供的现成接口 `https://api.prprpr.me/dplayer/`。

然后修改配置文件：

```toml
[http]
danmaku_api_url = "https://api.prprpr.me/dplayer/"
```

设置你的 bgmi_http，享受弹幕支援吧。

## 调试

log 文件位于 `{BGMI_PATH}/log/`。

## 卸载

由于 pip 的限制，你需要手动清理 BGmi 产生的位于 `~/.bgmi` 的文件。

同样，BGmi 添加到你系统的定时任务也不会被自动删除，请手动删除。

*nix：

    请手动清理 crontab

Windows：

```bash
schtasks /Delete /TN 'bgmi updater'
```

## Bangumi Script

如果你对 Python 有一点了解，并且觉得还不够的话，下面是为你准备的。

你可以写一个 BGmi Script 来解析你自己想看的番剧或者美剧。BGmi 会加载你的 script，视作一个番剧来对待。你所需要做的只是继承 `ScriptBase` 类，然后实现特定的方法，再把你的 script 文件放到 `BGMI_PATH/script` 文件夹内。

Example：[./tests/script_example.py](./tests/script_example.py)

`get_download_url()` 返回一个 `dict`，以对应集数为键，对应的下载链接为值：

```python
{
  1: 'http://example.com/Bangumi/1/1.mp4',
  2: 'http://example.com/Bangumi/1/2.torrent',
  3: 'http://example.com/Bangumi/1/3.mp4'
}
```

### 加载 scripts

注意，scripts 只会在运行 `bgmi update` 或者 `bgmi cal` 时被加载。如果你在 Web UI 找不到对应的内容，请运行上述命令并重试。

## BGmi 数据源

通过扩展 `bgmi.website.base.BaseWebsite` 类并且实现对应的三个方法，你也可以简单地添加一个数据源。

每个方法具体的意义和返回值格式请参照每个方法对应的注释：

```python
from typing import List, Optional

from bgmi.website.base import BaseWebsite
from bgmi.website.model import Episode, WebsiteBangumi


class DataSource(BaseWebsite):
  def search_by_keyword(
    self, keyword: str, count: int
  ) -> List[Episode]:
    """
    :param keyword: search key word
    :param count: how many page to fetch from website
    :return: list of episode search result
    """
    raise NotImplementedError

  def fetch_bangumi_calendar(self) -> List[WebsiteBangumi]:
    """
    return a list of all bangumi and a list of all subtitle group

    list of bangumi dict:
    update time should be one of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Unknown']
    """
    raise NotImplementedError

  def fetch_episode_of_bangumi(
    self, bangumi_id: str, max_page: int, subtitle_list: Optional[List[str]] = None
  ) -> List[Episode]:
    """
    get all episode by bangumi id

    :param bangumi_id: bangumi_id
    :param subtitle_list: list of subtitle group
    :param max_page: how many page you want to crawl if there is no subtitle list
    :return: list of bangumi
    """
    raise NotImplementedError

  def fetch_single_bangumi(self, bangumi_id: str) -> WebsiteBangumi:
    """
    fetch bangumi info when updating

    :param bangumi_id: bangumi_id, or bangumi['keyword']
    """
    # return WebsiteBangumi(keyword=bangumi_id) if website don't has a page contains episodes and info
```

## MCP（Model Context Protocol）支持

`bgmi_http` 内置了 [MCP](https://modelcontextprotocol.io/) 服务端，允许 MCP 客户端直接管理追番订阅。

### 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/mcp` | POST | Streamable HTTP（Codex 等客户端） |
| `/mcp/sse` | GET | SSE 长连接（MCP 传输层） |
| `/mcp/messages` | POST | 发送 JSON-RPC 消息 |

### 认证

所有请求需携带 `Authorization: Bearer <token>` HTTP Header，token 为 `~/.bgmi/config.toml` 中 `[http]` 下的 `admin_token`。

### 可用 Tools

| Tool | 说明 |
|---|---|
| `cal` | 获取当前季度番剧日历 |
| `list` | 列出我的订阅 |
| `add` | 订阅番剧（支持 `season` 设置季度，对已订阅番剧同样有效） |
| `delete` | 取消订阅 |
| `search` | 搜索番剧 |
| `update` | 检查更新并下载 |
| `seen` | 获取已观看集数列表 |
| `seen_forget` | 移除单集下载记录（触发重新下载） |
| `seen_mark` | 添加单集下载记录（标记为已观看） |
| `download` | 手动触发下载 |
| `download_status` | 查看下载任务状态 |
| `get_filter` | 获取过滤器配置 |
| `set_filter` | 设置过滤器 |
| `postprocess` | 整理已完成下载 |
| `set_status` | 修正订阅生命周期状态 |

### Agent 接入配置

在你的 AI 工具（Claude Desktop／Cursor／Cline）的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "bgmi": {
      "transport": "sse",
      "url": "http://<host>:8888/mcp/sse",
      "headers": {
        "Authorization": "Bearer <your-admin-token>"
      }
    }
  }
}
```

将 `<host>` 替换为服务器地址，`<your-admin-token>` 替换为 `~/.bgmi/config.toml` 中的值。

Codex 使用 Streamable HTTP，配置 URL 为 `/mcp`：

```toml
[mcp_servers.bgmi]
url = "http://<host>:8888/mcp"
http_headers = { "Authorization" = "Bearer <your-admin-token>" }
```

### 快速验证

```bash
# 启动服务
bgmi_http

# 测试连接（应返回 SSE endpoint 事件）
curl -N -H "Authorization: Bearer <token>" http://127.0.0.1:8888/mcp/sse

# 无认证应返回 401
curl http://127.0.0.1:8888/mcp/sse
```

## License

[MIT License](./LICENSE)
