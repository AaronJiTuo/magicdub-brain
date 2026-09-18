"""Bounded OpenRouter TTS verification, with an in-memory credential bridge."""
import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import threading
import time
import wave
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import httpx

MODELS = {'fish-audio/s2.1-pro', 'fish-audio/s2.1-pro-free:free'}
BASE = 'https://openrouter.ai/api/v1'


def now():
    return datetime.now(timezone.utc).isoformat()


def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inspect(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(p)], capture_output=True, text=True)
    data = json.loads(r.stdout)
    s = data['streams'][0]
    check = subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(p), '-f', 'null', '-'], capture_output=True, text=True)
    return {'duration': float(data['format']['duration']), 'sample_rate': int(s['sample_rate']),
            'channels': s['channels'], 'codec': s['codec_name'], 'sha256': sha(p),
            'decode_ok': check.returncode == 0, 'decode_error': check.stderr[:1000]}


def serve(out, baseline, port):
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((baseline / 'manifest.json').read_text())
    cases = {c['case_id']: c for c in manifest['cases']}
    state = {'key': None, 'running': False, 'requests': len(list((out / 'requests').glob('*/receipt.json')))}
    lock = threading.Lock()

    def usage(label):
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            r = client.get(BASE + '/auth/key', headers={'Authorization': 'Bearer ' + state['key']})
            d = r.json().get('data', {}) if r.status_code == 200 else {}
            result = {'checked_at': now(), 'http_status': r.status_code,
                      **{k: d.get(k) for k in ('usage', 'usage_daily', 'limit', 'limit_remaining', 'is_free_tier')}}
            save(out / ('usage-' + label + '.json'), result)
            return result

    def run(spec):
        ident = spec['id']
        assert re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', ident)
        model = spec['model']
        assert model in MODELS
        case = cases[spec['case_id']]
        dst = out / 'requests' / ident
        if dst.exists():
            raise ValueError('Request ID already exists; preserved without resubmission')
        assert state['requests'] < 30
        payload = {'model': model, 'input': spec.get('input', case['translated_text']),
                   'response_format': spec.get('response_format', 'mp3')}
        assert len(payload['input'].encode('utf-8')) <= 1000
        reference = (baseline / case['source_relative']).read_bytes()
        mode = spec.get('reference_mode', 'normal')
        if mode != 'none':
            audio = reference if mode != 'invalid' else b'NOT AN AUDIO FILE'
            payload['input_references'] = [{'type': 'input_audio', 'input_audio': {'data': 'data:audio/wav;base64,' + base64.b64encode(audio).decode()}}, {'type': 'text', 'text': case['source_text']}]
            if mode == 'multiple':
                payload['input_references'].append(payload['input_references'][0])
        for k in ('provider', 'speed', 'voice'):
            if k in spec:
                payload[k] = spec[k]
        dst.mkdir(parents=True)
        state['requests'] += 1
        safe = {k: v for k, v in payload.items() if k != 'input_references'}
        safe['reference'] = {'mode': mode, 'sha256': hashlib.sha256(reference).hexdigest(),
                             'duration': case['reference']['duration'], 'source_text': case['source_text']}
        receipt = {'id': ident, 'case_id': case['case_id'], 'status': 'pending', 'started_at': now(),
                   'request': safe, 'input_utf8_bytes': len(payload['input'].encode()), 'input_characters': len(payload['input'])}
        save(dst / 'receipt.json', receipt)
        started = time.monotonic()
        try:
            with httpx.Client(timeout=httpx.Timeout(180, connect=30), follow_redirects=False) as client:
                with client.stream('POST', BASE + '/audio/speech', headers={'Authorization': 'Bearer ' + state['key']}, json=payload) as r:
                    receipt.update(http_status=r.status_code, headers_seconds=round(time.monotonic()-started, 3),
                                   response_headers={k:v for k,v in r.headers.items() if k in ('content-type','x-generation-id','x-request-id','transfer-encoding','content-length','x-audio-sample-rate','x-audio-channels')})
                    chunks = []
                    for block in r.iter_bytes():
                        if block and not chunks:
                            receipt['first_audio_bytes_seconds'] = round(time.monotonic()-started, 3)
                        chunks.append(block)
                    content = b''.join(chunks)
                receipt.update(elapsed_seconds=round(time.monotonic()-started,3), response_bytes=len(content), chunk_count=len(chunks))
                if r.status_code == 200 and r.headers.get('content-type','').startswith('audio/'):
                    fmt = payload['response_format']
                    output = dst / ('output.' + fmt)
                    output.write_bytes(content)
                    receipt['status'] = 'generated'
                    if fmt == 'mp3':
                        receipt['audio'] = inspect(output)
                    elif fmt == 'pcm':
                        ct = r.headers.get('content-type', '')
                        rate = re.search(r'rate=(\d+)', ct)
                        channels = re.search(r'channels=(\d+)', ct)
                        if rate and channels:
                            wav = dst / 'output.wav'
                            with wave.open(str(wav), 'wb') as w:
                                w.setnchannels(int(channels[1])); w.setsampwidth(2); w.setframerate(int(rate[1])); w.writeframes(content)
                            receipt['audio'] = inspect(wav)
                        else:
                            receipt['pcm_metadata_missing'] = True
                    generation = r.headers.get('x-generation-id')
                    if generation:
                        gr = client.get(BASE + '/generation', params={'id': generation}, headers={'Authorization': 'Bearer ' + state['key']})
                        receipt['generation_lookup_status'] = gr.status_code
                        if gr.status_code == 200:
                            gd = gr.json().get('data', {})
                            receipt['generation'] = {k:gd.get(k) for k in ('id','model','provider_name','total_cost','is_byok','streamed','generation_time','latency','native_tokens_prompt','tokens_prompt','native_tokens_completion','tokens_completion')}
                else:
                    receipt.update(status='rejected', error=content.decode(errors='replace')[:6000].replace(state['key'], '[REDACTED]'))
        except Exception as e:
            receipt.update(status='unknown_do_not_retry', error_type=type(e).__name__, elapsed_seconds=round(time.monotonic()-started,3))
        save(dst / 'receipt.json', receipt)
        print(json.dumps({k: receipt.get(k) for k in ('id', 'status', 'http_status', 'elapsed_seconds')}, ensure_ascii=False), flush=True)
        return receipt

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, data, kind='application/json'):
            body = data if isinstance(data,str) else json.dumps(data,ensure_ascii=False)
            self.send_response(status)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body.encode())

        def do_GET(self):
            if self.path == '/credential':
                self.reply(200, '<!doctype html><meta charset="utf-8"><title>OpenRouter 临时测试</title><h1>OpenRouter 临时测试凭据</h1><p>Key 仅保留在本机进程内存，仅用于 OpenRouter API。</p><form method="post" action="/credential" autocomplete="off"><input type="password" name="key" aria-label="临时 API Key" autocomplete="off"><button>用于本轮测试</button></form>', 'text/html')
            elif self.path == '/status':
                self.reply(200, {'credential_ready': bool(state['key']), 'requests':state['requests'], 'running': state['running']})
            else:
                super().do_GET()

        def do_POST(self):
            host = f'127.0.0.1:{port}'
            if self.headers.get('Host') != host or self.headers.get('Origin', 'http://' + host) != 'http://' + host:
                self.reply(403, {'error':'Invalid origin/host'}); return
            raw = self.rfile.read(min(int(self.headers.get('Content-Length',0)), 10000))
            if self.path == '/credential' and not state['key']:
                key = parse_qs(raw.decode()).get('key',[''])[0].strip()
                if not re.fullmatch(r'sk-or-v1-[a-f0-9]+', key):
                    self.reply(400, {'error':'Invalid key format'}); return
                state['key'] = key
                self.reply(200, '<meta charset="utf-8"><h1>临时凭据已接收</h1><p>仅在本机进程内存中使用。</p>', 'text/html')
            elif self.path in ('/run','/usage') and state['key']:
                if not lock.acquire(blocking=False):
                    self.reply(409, {'error':'Busy'}); return
                state['running'] = True
                try:
                    data = json.loads(raw)
                    self.reply(200, run(data) if self.path == '/run' else usage(data['label']))
                except Exception as e:
                    self.reply(400, {'error_type': type(e).__name__})
                finally:
                    state['running'] = False
                    lock.release()
            elif self.path == '/finish':
                state['key'] = None
                self.reply(200, {'credential_cleared': True})
                threading.Thread(target=server.shutdown, daemon=True).start()
            else:
                self.reply(409, {'error':'Unavailable'})

    server = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler,directory=str(out)))
    print(f'Listening on http://127.0.0.1:{port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--port',type=int,default=8773)
    args = p.parse_args()
    serve(args.output,args.baseline,args.port)
