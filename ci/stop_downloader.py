import os
import sys

if sys.version_info > (3, 0):
    # python3
    from xmlrpc.client import ServerProxy
else:
    from xmlrpclib import ServerProxy

HOME = os.environ.get('HOME')
if os.environ.get('DOWNLOADER') == 'aria2-rpc':
    s = ServerProxy('http://localhost:6800/rpc')
    print(s.aria2.tellActive())
    s.aria2.shutdown()
    os.system('sudo pkill aria2c')
elif os.environ.get('DOWNLOADER') == 'tranmission-rpc':
    import transmissionrpc
    tc = transmissionrpc.Client('localhost', port=9091)
    print(tc.get_torrents())
    os.system('service transmission-daemon stop')
