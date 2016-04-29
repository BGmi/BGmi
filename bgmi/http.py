# coding=utf-8
import os
import BaseHTTPServer
from bgmi.utils import print_success


class TorrentFeedHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        file_path = os.path.join(os.path.dirname(__file__), '../download.xml')
        if os.path.exists(file_path):
            content_type = 'text/xml'
            with open(file_path, 'r') as f:
                data = f.read()
        else:
            content_type = 'text/html'
            data = 'download.xml not exist'
        self.send_response(200)
        self.send_header("Content-type", "%s; charset=utf-8" % content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(port):
    print_success('BGmi HTTP Server start on port %d' % port)
    server = BaseHTTPServer.HTTPServer(('', port), TorrentFeedHandler)
    server.serve_forever()
