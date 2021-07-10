from bgmi.downloader import DelugeRPC

client = DelugeRPC()

# deluge的Web需要进行初始化
# 但是用户的deluge应该已经初始化过了
# 只需要在测试环境中进行

if not client._call("web.connected"):
    connected_web = client._call("web.get_hosts")
    host = connected_web[0][1]
    client._call("web.connect", params=[host])
