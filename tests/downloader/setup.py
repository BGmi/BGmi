from bgmi.downloader import DelugeRPC

client = DelugeRPC()

if not client._call("web.connected"):
    connected_web = client._call("web.get_hosts")
    host = connected_web[0][1]
    client._call("web.connect", params=[host])
