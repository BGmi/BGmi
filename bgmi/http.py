# coding=utf-8
from __future__ import print_function, unicode_literals
from bgmi.config import IS_PYTHON3
from bgmi.utils import print_success, download_xml
from bgmi.models import Download


def process_data(data):
    return data

if IS_PYTHON3:
    from http.server import BaseHTTPRequestHandler, HTTPServer

    def process_data(data):
        return bytes(data, 'utf-8')
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class TorrentFeedHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = download_xml(Download.get_all_downloads())
        content_type = 'text/xml'
        self.send_response(200)
        self.send_header("Content-type", "%s; charset=utf-8" % content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(process_data(data))


def main(port):
    print_success('BGmi HTTP Server start on port %d' % port)
    server = HTTPServer(('', port), TorrentFeedHandler)
    server.serve_forever()
