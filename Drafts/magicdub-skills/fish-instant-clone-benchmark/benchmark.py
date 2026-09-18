"""Bounded Fish S2.1 Pro instant-clone experiment; never changes source projects."""
import argparse
import functools
import hashlib
import json
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import msgpack
import numpy as np
import soundfile as sf

ROOT = Path.home() / 'Movies/MagicDub'
SELECTION = [
    ('youtube-HC4lPDHT15A_20260918_1504', ['s0001', 's0007', 's0012', 's0004', 's0000', 's0005']),
    ('youtube-qmMIk13HOLQ_20260918_1627', ['s0067', 's0066', 's0000']),
    ('youtube-uDCm_OZ_b30_20260918_1635', ['s0019', 's0000', 's0006']),
]


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path):
    data, rate = sf.read(path, always_2d=True)
    assert data.size and np.isfinite(data).all(), path
    info = sf.info(path)
    return dict(duration=round(len(data)/rate, 6), frames=len(data), sample_rate=rate,
                channels=data.shape[1], subtype=info.subtype,
                rms=float(np.sqrt(np.mean(data**2))), peak=float(np.max(np.abs(data))),
                sha256=sha(path))


def prepare(out, model='s2.1-pro'):
    if (out/'manifest.json').exists():
        raise SystemExit('Manifest already exists; choose another output or use serve.')
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    for project, ids in SELECTION:
        p = ROOT/project
        rows = {r['id']:r for r in json.loads((p/'alignment.json').read_text())['segments']}
        for sid in ids:
            row = rows[sid]
            case = f'{len(cases)+1:02d}_{project.split("_")[0][8:]}_{sid}'
            dst = out/'samples'/case
            dst.mkdir(parents=True, exist_ok=False)
            original = p/row.get('original_reference_artifact', row['reference_artifact'])
            files = {'source.wav':original, 'index.wav':p/row['tts_artifact']}
            for name, source in files.items():
                shutil.copy2(source,dst/name)
            ref = inspect(dst/'source.wav')
            target_duration = (row['end_ms']-row['start_ms'])/1000
            assert abs(ref['duration']-target_duration)<.002, (case,ref,target_duration)
            assert ref['rms']>=1e-5, (case,'silent')
            cases.append(dict(case_id=case, project=project, segment_id=sid,
                speaker=row.get('speaker'), start_ms=row['start_ms'], end_ms=row['end_ms'],
                source_text=row['source_text'], translated_text=row['translated_text'],
                reference=ref, source_path=str(original), source_alignment_sha256=sha(p/'alignment.json'),
                index=inspect(dst/'index.wav'), index_reference=row['reference_artifact'],
                source_relative=f'samples/{case}/source.wav', index_relative=f'samples/{case}/index.wav',
                fish_relative=f'samples/{case}/fish.wav',
                target_utf8_bytes=len(row['translated_text'].encode('utf-8'))))
    manifest = dict(created_at=datetime.now(timezone.utc).isoformat(), model=model,
        endpoint='https://api.fish.audio/v1/tts', mode='instant clone; inline reference audio and source text',
        reference_processing='none; unpadded original per-sentence references copied byte-for-byte',
        parameters=dict(format='wav', sample_rate=44100, latency='normal', temperature=.7, top_p=.7,
                        prosody=dict(speed=1., volume=0, normalize_loudness=True)),
        price_usd_per_million_utf8_bytes=0 if model.endswith('-free') else 15, usd_cny=7, cases=cases)
    save(out/'manifest.json',manifest)
    print(json.dumps(dict(cases=len(cases), short_cases=[(r['case_id'],r['reference']['duration']) for r in cases if r['reference']['duration']<.5], target_bytes=sum(r['target_utf8_bytes'] for r in cases), output=str(out)),ensure_ascii=False),flush=True)


def run_batch(out, key):
    manifest=json.loads((out/'manifest.json').read_text())
    headers={'Authorization':f'Bearer {key}','model':manifest['model'],'Content-Type':'application/msgpack'}
    def wallet(client,label):
        try:
            r=client.get('https://api.fish.audio/wallet/self/api-credit',headers={'Authorization':headers['Authorization']})
            data=r.json() if r.status_code==200 else {}
            item=dict(http_status=r.status_code,credit=data.get('credit'),checked_at=datetime.now(timezone.utc).isoformat())
        except Exception as e:
            item={'error_type':type(e).__name__}
        save(out/f'wallet-{label}.json',item)
        return item
    with httpx.Client(timeout=httpx.Timeout(180,connect=30),follow_redirects=False) as client:
        before=wallet(client,'before')
        print(json.dumps({'wallet_before':before},ensure_ascii=False),flush=True)
        for c in manifest['cases']:
            dst=out/'samples'/c['case_id']; meta=dst/'result.json'
            if meta.exists():
                print('PRESERVED '+c['case_id'],flush=True)
                continue
            data=dict(case_id=c['case_id'],status='sending',started_at=datetime.now(timezone.utc).isoformat(),model=manifest['model'],target_utf8_bytes=c['target_utf8_bytes'])
            save(meta,data)
            payload=dict(manifest['parameters'],text=c['translated_text'],references=[dict(audio=(dst/'source.wav').read_bytes(),text=c['source_text'])])
            started=time.monotonic()
            try:
                r=client.post(manifest['endpoint'],headers=headers,content=msgpack.packb(payload,use_bin_type=True))
                data.update(http_status=r.status_code,elapsed_seconds=round(time.monotonic()-started,3),response_headers={k:v for k,v in r.headers.items() if k in ['content-type','x-request-id','request-id','x-model','model','x-character-count','x-usage','x-billable-characters','x-billable-bytes']})
                if r.status_code==200 and r.content[:4] in [b'RIFF',b'RF64']:
                    (dst/'fish.wav').write_bytes(r.content)
                    data.update(status='generated',audio=inspect(dst/'fish.wav'))
                    data['duration_ratio']=round(data['audio']['duration']/c['reference']['duration'],4)
                    check=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(dst/'fish.wav'),'-f','null','-'],capture_output=True,text=True)
                    data['decode_ok']=check.returncode==0
                    if check.returncode: data['status']='decode_failed'
                else:
                    data.update(status='rejected',error=r.text[:1200].replace(key,'[REDACTED]'))
                save(meta,data)
                print(json.dumps(data,ensure_ascii=False),flush=True)
                if r.status_code in [401,402,403,429]:
                    break
            except Exception as e:
                data.update(status='unknown_do_not_retry',error_type=type(e).__name__,elapsed_seconds=round(time.monotonic()-started,3))
                save(meta,data); print(json.dumps(data),flush=True)
                break
        after=wallet(client,'after')
        print(json.dumps({'wallet_after':after},ensure_ascii=False),flush=True)
    key=None


def serve(out,port):
    state={'key':None,'running':False,'done':False}
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,code,body,kind='text/html; charset=utf-8'):
            self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body.encode())
        def do_GET(self):
            if self.path=='/credential':
                self.reply(200,'<!doctype html><meta charset="utf-8"><title>Fish 本地测试凭据</title><h1>Fish 本地测试</h1><p>密钥仅在本地进程内存中使用，仅发送到 api.fish.audio。</p><form method="post" action="/credential" autocomplete="off"><label>临时 API Key <input aria-label="临时 API Key" type="password" name="key" autocomplete="off"></label><button>用于本轮测试</button></form>')
            elif self.path=='/status':
                self.reply(200,json.dumps(dict(credential_ready=bool(state['key']),running=state['running'],done=state['done'])),'application/json')
            else: super().do_GET()
        def do_POST(self):
            if self.headers.get('Host')!=f'127.0.0.1:{port}':
                self.reply(403,'Invalid host');return
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://127.0.0.1:{port}':
                self.reply(403,'Invalid origin');return
            raw=self.rfile.read(min(int(self.headers.get('Content-Length',0)),4096))
            if self.path=='/credential' and not state['running']:
                key=parse_qs(raw.decode()).get('key',[''])[0].strip()
                if not key.startswith('sk-fish-'):
                    self.reply(400,'Key format invalid');return
                state['key']=key
                self.reply(200,'<meta charset="utf-8"><h1>已接收临时凭据</h1><p>密钥仅保留在本轮进程内存中。</p>')
            elif self.path=='/start' and state['key'] and not state['running'] and not state['done']:
                state['running']=True
                def worker():
                    try: run_batch(out,state['key'])
                    finally: state.update(key=None,running=False,done=True)
                threading.Thread(target=worker,daemon=True).start();self.reply(202,'Started')
            else:self.reply(409,'Unavailable')
    server=ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Handler,directory=str(out)))
    print(f'Listening on http://127.0.0.1:{port}',flush=True)
    server.serve_forever()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['prepare','serve']);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--port',type=int,default=8766);ap.add_argument('--model',choices=['s2.1-pro','s2.1-pro-free'],default='s2.1-pro');args=ap.parse_args()
    if args.command=='prepare': prepare(args.output,args.model)
    else: serve(args.output,args.port)
