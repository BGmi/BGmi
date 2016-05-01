# coding=utf-8
from __future__ import print_function, unicode_literals
import BaseHTTPServer
from bgmi.utils import print_success, download_xml
from bgmi.models import Download


class TorrentFeedHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        data = download_xml(Download.get_all_downloads())
        content_type = 'text/xml'
        self.send_response(200)
        self.send_header("Content-type", "%s; charset=utf-8" % content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(port):
    print_success('BGmi HTTP Server start on port %d' % port)
    server = BaseHTTPServer.HTTPServer(('', port), TorrentFeedHandler)
    server.serve_forever()
