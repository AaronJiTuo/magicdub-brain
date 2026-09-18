"""Loopback preview with HTTP Range support for accurate audio seeking."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from urllib.parse import urlparse


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def list_directory(self, path):
        self.send_error(403)

    def send_head(self):
        self.byte_range = None
        url_path = urlparse(self.path).path
        if url_path != '/index.html' and not re.fullmatch(r'/review/[a-z_]+\.(wav|flac)', url_path):
            self.send_error(404)
            return None
        path = Path(self.translate_path(self.path))
        value = self.headers.get('Range')
        if not value or not path.is_file():
            return super().send_head()
        match = re.fullmatch(r'bytes=(\d+)-(\d*)', value)
        if not match:
            self.send_error(416)
            return None
        size = path.stat().st_size
        start = int(match[1])
        end = min(int(match[2]) if match[2] else size-1, size-1)
        if start > end or start >= size:
            self.send_error(416)
            return None
        f = path.open('rb')
        f.seek(start)
        self.byte_range = end-start+1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(self.byte_range))
        self.end_headers()
        return f

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def copyfile(self, source, outputfile):
        try:
            if self.byte_range is None:
                return super().copyfile(source, outputfile)
            left = self.byte_range
            while left:
                block = source.read(min(left, 65536))
                if not block:
                    break
                outputfile.write(block)
                left -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--port',type=int,default=8769)
    args=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(args.output)))
    print(f'Listening on http://127.0.0.1:{args.port}/index.html',flush=True)
    server.serve_forever()
