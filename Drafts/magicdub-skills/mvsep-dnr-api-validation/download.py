"""Download only the saved result's three stems; never submit another job."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlparse

import requests

out = Path(sys.argv[1])
result = json.loads((out/'result.json').read_text())
assert result['success'] and result['status'] == 'done'
assert result['data']['algorithm'] == 'MVSep DnR v3 (speech, music, effects)'
files = result['data']['files']
assert {f['type'].lower() for f in files} == {'speech', 'music', 'sfx'}
(out/'stems').mkdir(exist_ok=True)


def download(item):
    stem = item['type'].lower()
    u = urlparse(item['url'])
    assert u.scheme == 'https' and u.hostname == 'hk.mvsep.com'
    assert '_mt_2_' in u.path  # provider confirms Mel+SCNet result naming
    target = out/'stems'/f'{stem}.wav'
    started = time.monotonic()
    if not (target.exists() and target.stat().st_size == item['bytes']):
        temp = target.with_suffix('.partial')
        for attempt in range(3):
            try:
                with requests.get(item['url'], stream=True, timeout=(30, 90)) as response:
                    response.raise_for_status()
                    with temp.open('wb') as f:
                        for chunk in response.iter_content(1024*256):
                            f.write(chunk)
                if temp.stat().st_size != item['bytes']:
                    raise ValueError('Download size mismatch')
                temp.replace(target)
                break
            except (requests.RequestException, ValueError):
                if attempt == 2:
                    raise
                time.sleep(2)
    return dict(stem=stem, bytes=target.stat().st_size,
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                download_seconds=time.monotonic()-started)


with ThreadPoolExecutor(max_workers=3) as pool:
    receipts = list(pool.map(download, files))
(out/'downloads.json').write_text(json.dumps(receipts, indent=2)+'\n')
print(json.dumps(receipts))
