"""Fix only placeholder sizes in streamed PCM WAV responses; preserve exact audio bytes."""
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

from benchmark import inspect, save


def finalize(out):
    results=[]
    for p in sorted((out/'samples').glob('*/result.json')):
        r=json.loads(p.read_text());wav=p.parent/'fish.wav'
        if not wav.exists():continue
        b=wav.read_bytes()
        if (b[:4]==b'RIFF' and b[8:12]==b'WAVE' and b[12:16]==b'fmt ' and
                struct.unpack('<I',b[16:20])[0]==16 and b[36:40]==b'data' and
                struct.unpack('<I',b[4:8])[0]==0xffffff24 and
                struct.unpack('<I',b[40:44])[0]==0xffffff00):
            assert (len(b)-44)%struct.unpack('<H',b[32:34])[0]==0
            raw=p.parent/'fish-response.wav';assert not raw.exists()
            wav.rename(raw)
            fixed=b[:4]+struct.pack('<I',len(b)-8)+b[8:40]+struct.pack('<I',len(b)-44)+b[44:]
            assert fixed[44:]==b[44:]
            wav.write_bytes(fixed)
            save(p.parent/'result-before-header-repair.json',r)
            r.update(original_response_audio=r['audio'],audio=inspect(wav),header_repair=dict(
                reason='Response WAV uses placeholder RIFF/data lengths (0xffffff24/0xffffff00)',
                only_modified_byte_ranges=[[4,8],[40,44]],audio_payload_identical=True,
                pcm_payload_sha256=hashlib.sha256(b[44:]).hexdigest(),original_file='fish-response.wav'))
        check=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(wav),'-f','null','-'],capture_output=True,text=True)
        r['decode_ok']=check.returncode==0;r['status']='generated' if r['decode_ok'] else 'decode_failed'
        if check.returncode:r['decode_error']=check.stderr[:1000]
        save(p,r);results.append({'case_id':r['case_id'],'decode_ok':r['decode_ok'],'header_repaired':'header_repair' in r,'duration':r['audio']['duration']})
    print(json.dumps(results,ensure_ascii=False))


if __name__=='__main__':finalize(Path(sys.argv[1]))
