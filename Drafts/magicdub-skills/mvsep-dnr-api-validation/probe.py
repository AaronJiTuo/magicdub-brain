"""One explicitly requested MVSep experiment; credentials never reach disk."""
import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import parse_qs, urlparse

import requests

BASE = 'https://hk.mvsep.com/api'
PARAMS = dict(sep_type='56', add_opt1='2', add_opt2='0', add_opt3='0',
              output_format='1', is_demo='0')


def now():
    return datetime.now(timezone.utc).isoformat()


def save(out, name, value):
    target = out / name
    temp = target.with_suffix(target.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(target)


def safe(value, key):
    if isinstance(value, dict):
        return {k: safe(v, key) for k, v in value.items()
                if k.lower() not in {'api_token', 'token', 'password', 'email', 'name'}}
    if isinstance(value, list):
        return [safe(v, key) for v in value]
    return value.replace(key, '[REDACTED]') if isinstance(value, str) and key else value


def account(session, key):
    r = session.get(BASE + '/app/user', params={'api_token': key}, timeout=40)
    j = r.json()
    d = j.get('data', {})
    return dict(at=now(), http_status=r.status_code, success=j.get('success'),
                **{k: d.get(k) for k in ('premium_minutes', 'premium_enabled')})


def run(out, key):
    session = requests.Session()  # default adapter has no automatic POST retries
    try:
        before = account(session, key)
        save(out, 'account-before.json', before)
        print(json.dumps({'account_before': before}), flush=True)
        if not before['success']:
            raise RuntimeError('Account preflight failed')
        # This experiment is authorized only against the account's free allowance.
        if before['premium_enabled'] in (1, '1') and float(before['premium_minutes'] or 0) > 0:
            raise RuntimeError('Paid usage enabled with positive balance; stop for budget review')
        attempt = dict(started_at=now(), base_url=BASE, parameters=PARAMS,
                       status='submission_unknown', automatic_create_retries=0)
        with (out / 'attempt.json').open('x') as f:
            json.dump(attempt, f, indent=2)
        start = time.monotonic()
        with (out / 'original.wav').open('rb') as audio:
            r = session.post(BASE + '/separation/create', data={**PARAMS, 'api_token': key},
                             files={'audiofile': ('stevejobs-first60-mvsep-test.wav', audio, 'audio/wav')},
                             timeout=(30, 180), allow_redirects=False)
        try:
            response = safe(r.json(), key)
        except ValueError:
            response = dict(non_json=True, excerpt=safe(r.text[:500], key))
        save(out, 'submission.json', dict(at=now(), elapsed_seconds=time.monotonic()-start,
                                         http_status=r.status_code, response=response))
        print(json.dumps({'submission_http': r.status_code, 'response': response}), flush=True)
        job = response.get('data', {}).get('hash')
        if not response.get('success') or not job:
            attempt['status'] = 'rejected' if response.get('success') is False else 'submission_unknown'
            save(out, 'attempt.json', attempt)
            return
        attempt.update(status='accepted', hash=job)
        save(out, 'attempt.json', attempt)
        previous = None
        for _ in range(240):
            try:
                r = session.get(BASE + '/separation/get', params={'hash': job}, timeout=40)
                r.raise_for_status()
                result = safe(r.json(), key)
            except Exception as exc:
                with (out / 'poll-events.jsonl').open('a') as f:
                    f.write(json.dumps(dict(at=now(), error_type=type(exc).__name__))+'\n')
                time.sleep(15)
                continue
            event = dict(at=now(), elapsed_seconds=time.monotonic()-start,
                         status=result.get('status'), data=result.get('data'))
            with (out / 'poll-events.jsonl').open('a') as f:
                f.write(json.dumps(event, ensure_ascii=False)+'\n')
            save(out, 'status.json', result)
            state = result.get('status')
            if state != previous:
                print(json.dumps({'state': state, 'elapsed_seconds': event['elapsed_seconds'],
                                  'message': (result.get('data') or {}).get('message')}), flush=True)
                previous = state
            if state in ('done', 'failed', 'not_found'):
                save(out, 'result.json', result)
                save(out, 'timing.json', dict(submission_to_terminal_seconds=event['elapsed_seconds'],
                                            terminal_status=state, completed_at=now()))
                break
            time.sleep(15)
        else:
            print('Polling window ended; resume by saved hash, do not resubmit.', flush=True)
    except Exception as exc:
        # Avoid exception strings: requests exceptions can contain authenticated URLs.
        save(out, 'error.json', dict(at=now(), type=type(exc).__name__,
                                    message='Inspect saved receipt; never automatically repeat POST.'))
        print(json.dumps({'error_type': type(exc).__name__}), flush=True)
    finally:
        try:
            after = account(session, key)
            save(out, 'account-after.json', after)
            print(json.dumps({'account_after': after}), flush=True)
        except Exception:
            print('Post-run account check unavailable.', flush=True)
        session.close()


def serve(out, port):
    state = dict(key=None, running=False, done=False)
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def reply(self, code, text, kind='text/html; charset=utf-8'):
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(text.encode())
        def do_GET(self):
            if self.path == '/credential':
                self.reply(200, '<!doctype html><meta charset="utf-8"><title>MVSep 临时凭据</title>'
                           '<h1>MVSep 本轮 API 测试</h1><p>Key 仅保留于本机进程内存。</p>'
                           '<form method="post" action="/credential" autocomplete="off">'
                           '<label>临时 API Key <input name="key" type="password" autocomplete="off"></label>'
                           '<button>用于本轮测试</button></form>')
            elif self.path == '/status':
                self.reply(200, json.dumps(dict(credential_ready=bool(state['key']),
                                               running=state['running'], done=state['done'])), 'application/json')
            else:
                self.reply(404, 'Not found')
        def do_POST(self):
            if self.headers.get('Host') != f'127.0.0.1:{port}' or self.headers.get('Origin') not in (None, f'http://127.0.0.1:{port}'):
                self.reply(403, 'Invalid origin'); return
            length = int(self.headers.get('Content-Length', 0))
            if length > 4096:
                self.reply(413, 'Too large'); return
            raw = self.rfile.read(length)
            with lock:
                if self.path == '/credential' and not state['running'] and not state['done']:
                    key = parse_qs(raw.decode()).get('key', [''])[0].strip()
                    if not key or len(key) > 512:
                        self.reply(400, 'Invalid key'); return
                    state['key'] = key
                    self.reply(200, '<meta charset="utf-8"><h1>临时凭据已接收</h1>')
                elif self.path == '/start' and state['key'] and not state['running'] and not state['done']:
                    if (out / 'attempt.json').exists():
                        self.reply(409, 'Existing attempt: do not repeat'); return
                    state['running'] = True
                    def worker():
                        try:
                            run(out, state['key'])
                        finally:
                            state.update(key=None, running=False, done=True)
                    threading.Thread(target=worker, daemon=True).start()
                    self.reply(202, 'Started')
                else:
                    self.reply(409, 'Unavailable')
    print(f'Listening on http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['prepare', 'serve'])
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--input', type=Path)
    ap.add_argument('--port', type=int, default=8768)
    args = ap.parse_args()
    if args.command == 'prepare':
        args.output.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(args.input, args.output / 'original.wav')
        save(args.output, 'manifest.json', dict(created_at=now(), sample='Steve Jobs first 60 seconds',
             source=str(args.input.resolve()), sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
             base_url=BASE, parameters=PARAMS, duration_seconds=60, sample_rate=44100, channels=2))
    else:
        serve(args.output, args.port)
