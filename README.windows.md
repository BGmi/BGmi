<!-- vscode-markdown-toc -->
* 1. [安装](#)
	* 1.1. [使用pip安装BGmi](#pipBGmi)
	* 1.2. [hello BGmi](#helloBGmi)
	* 1.3. [安装相应的插件](#-1)
	* 1.4. [一些BGmi设置](#BGmi)
* 2. [下载工具](#-1)
* 3. [自动更新](#-1)
	* 3.1. [在任务中搜索计划任务](#-1)
		* 3.1.1. [操作-添加基本计划任务](#-)
		* 3.1.2. [如果想要更精确的更新频率设置 找到相应的任务,右键-属性](#--1)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc --># BGmi windows support

##  1. <a name=''></a>安装

安装[python](https://www.python.org/downloads/windows/)后

使用cmd.exe或者powershell.exe运行以下命令
(如果你用的是git bash之类的话,请注意转义字符)

###  1.1. <a name='pipBGmi'></a>使用pip安装BGmi

```bash
pip install bgmi
bgmi
```

###  1.2. <a name='helloBGmi'></a>hello BGmi

```bash
bgmi -h
```

###  1.3. <a name='-1'></a>安装相应的插件

```bash
bgmi install
pip install transmissionrpc
```

###  1.4. <a name='BGmi'></a>一些BGmi设置

设置使用transmission下载
```bash
bgmi config DOWNLOAD_DELEGATE transmission-rpc
```

设置管理的token
```bash
bgmi config ADMIN_TOKEN your-token
```

设置视频文件存放地址
```bash
bgmi config SAVE_PATH E:\bangumi
```

可以将`E:\bangumi`替换成你想要保存番剧的文件夹



##  2. <a name='-1'></a>下载工具

BGmi在windows平台下暂不(可能永远也不会)支持迅雷, 请使用[transmission](https://transmissionbt.com/)

并且开启WebUI.

<!-- ### bgmi transmission support -->


##  3. <a name='-1'></a>自动更新

在安装的时候,已经提前释放好了自动更新脚本到`SAVE_PATH/cron.vbs`

因为windows的限制,请根据自己的情况手动添加计划任务,步骤如下

以win10为例,win7等请自行百度解决

###  3.1. <a name='-1'></a>在任务中搜索计划任务

![](https://ws1.sinaimg.cn/thumbnail/bd69bf14ly1fkax2n1y54j20b9073aa4.jpg)

####  3.1.1. <a name='-'></a>操作-添加基本计划任务

![1](https://ws1.sinaimg.cn/large/bd69bf14ly1fkawye9c9cj20oz0gl75p.jpg)
![2](https://ws1.sinaimg.cn/large/bd69bf14ly1fkawye75s0j20j90f9dg5.jpg)
![3](https://ws1.sinaimg.cn/large/bd69bf14ly1fkawye81ttj20ja0fdjrj.jpg)

`起始于`虽然说是可选,但是是必填的,请填写`cron.vbs`所在的文件夹

![4](https://ws1.sinaimg.cn/large/bd69bf14ly1fkawye77tgj20j80faaab.jpg)

####  3.1.2. <a name='--1'></a>如果想要更精确的更新频率设置 找到相应的任务,右键-属性

![5](https://ws1.sinaimg.cn/large/bd69bf14ly1fkawye9vs5j20vr0axmyr.jpg)
![6](https://ws1.sinaimg.cn/large/bd69bf14ly1fkawyewyitj20vk0gi7hx.jpg)


