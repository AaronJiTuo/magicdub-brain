"""Offline comparison, using identical playback gain and no per-track normalization."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess

import numpy as np

RATE = 48000
WINDOWS = [('讲话参考', 8.2, 12.6), ('笑话与观众反应', 16, 31), ('观众反应候选短窗', 26.8, 28.2)]


def read_audio(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
                                   '-ar', str(RATE), '-ac', '2', '-f', 'f32le', '-'])
    return np.frombuffer(raw, dtype='<f4').reshape(-1, 2).copy()


def write_audio(path, value):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(RATE), '-ac', '2',
                    '-i', '-', '-c:a', ('flac' if path.suffix == '.flac' else 'pcm_s16le'), str(path)],
                   input=value.astype('<f4').tobytes(), check=True)


def inspect(path):
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'], check=True)
    return dict(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                duration_seconds=float(info['format']['duration']),
                sample_rate=int(info['streams'][0]['sample_rate']),
                channels=info['streams'][0]['channels'], codec=info['streams'][0]['codec_name'],
                full_decode=True)


def rms(value):
    return float(np.sqrt(np.mean(value.astype(np.float64)**2)))


def main(out, baseline):
    audio = dict(original=read_audio(out/'original.wav'),
                 demucs_background=read_audio(baseline/'review/demucs_background.wav'),
                 tts=read_audio(baseline/'review/tts_reference.wav'))
    for stem in ('music', 'sfx', 'speech'):
        audio[stem] = read_audio(out/'stems'/f'{stem}.wav')
    lengths = {k: len(v) for k,v in audio.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(f'Timeline mismatch: {lengths}')
    audio['mvsep_background'] = audio['music']+audio['sfx']
    audio['demucs_dub'] = audio['demucs_background']+audio['tts']
    audio['mvsep_dub'] = audio['mvsep_background']+audio['tts']
    titles = dict(original='原始英文现场音', demucs_background='已有 Demucs 背景',
                  mvsep_background='MVSep 背景 · Music＋SFX', speech='MVSep · Speech',
                  music='MVSep · Music', sfx='MVSep · SFX',
                  demucs_dub='已有中文配音＋Demucs 背景', mvsep_dub='同一中文配音＋MVSep 背景')
    max_peak = max(float(np.max(np.abs(audio[k]))) for k in titles)
    gain = min(1.0, 0.98/max_peak) if max_peak > 0 else 1.0
    review = out/'review'
    review.mkdir(exist_ok=True)
    measurements = {}
    for k in titles:
        write_audio(review/f'{k}.flac', audio[k]*gain)
        write_audio(review/f'{k}.wav', audio[k]*gain)
        measurements[k] = dict(peak=float(np.max(np.abs(audio[k]))), windows=[])
        for label,start,end in WINDOWS:
            a,b = round(start*RATE),round(end*RATE)
            ref, signal = audio['original'][a:b], audio[k][a:b]
            measurements[k]['windows'].append(dict(label=label, start=start, end=end,
                rms=rms(signal), rms_relative_original_db=20*np.log10((rms(signal)+1e-12)/(rms(ref)+1e-12))))
    reconstruction = audio['music']+audio['sfx']+audio['speech']
    summary = dict(playback_gain=gain, measurements=measurements,
                   reconstruction_error_rms=rms(reconstruction-audio['original']),
                   note='Energy comparisons are not isolated speech/laughter quality scores.')
    (out/'analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    validation = [inspect(path) for path in [out/'original.wav', *sorted((out/'stems').glob('*.wav')), *sorted(review.glob('*.flac')), *sorted(review.glob('*.wav'))]]
    (out/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    cards = ''.join(f'<article><h2>{html.escape(title)}</h2><button class="track" data-src="review/{k}.wav" data-title="{html.escape(title)}">播放该音轨</button></article>' for k,title in titles.items())
    buttons = ''.join(f'<button data-start="{start}" data-end="{end}">{html.escape(label)} {start}–{end}s</button>' for label,start,end in WINDOWS)
    timing = json.loads((out/'timing.json').read_text())
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MVSep × Demucs 试听</title>
<style>body{margin:0;background:#f5f4f0;color:#25302d;font:16px/1.65 system-ui}main{max-width:1000px;margin:auto;padding:40px 24px}h1{font-size:36px;line-height:1.25}h2{font-size:17px;margin:0 0 16px}p{color:#59625f}article{background:white;border:1px solid #dddcd5;border-radius:14px;padding:24px}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}audio{width:100%}nav{display:flex;gap:8px;flex-wrap:wrap;margin:26px 0;position:sticky;top:0;padding:12px 0;background:#f5f4f0}button{cursor:pointer;padding:9px 13px;border:1px solid #abb6aa;background:#fff;border-radius:8px}button.selected{background:#295c48;color:#fff}.tag{letter-spacing:2px;color:#397356;font-size:13px}@media(max-width:700px){section{grid-template-columns:1fr}h1{font-size:28px}}</style><main>
<div class="tag">MAGICDUB / SEPARATION TEST</div><h1>MVSep DnR v3 · Mel＋SCNet</h1>
<p>Steve Jobs 前 60 秒。相同原音，与此前 Demucs 实测结果对照。重点听 Music＋SFX 背景里的讲话残留，以及笑声、掌声是否保留。</p>'''
    document += f'<p>免费账号真实 API 请求 1 次 · 提交至首次查到完成约 {timing["submission_to_terminal_seconds"]:.1f} 秒 · 三轨原始 WAV 已保留。</p><p>所有播放器统一增益 {gain:.6f}，没有逐轨响度归一化。网页试听副本统一为 48 kHz 双声道 PCM16 WAV，同时保留 FLAC；原始 MVSep 返回规格见报告。中文配音复用既有结果，本轮没有重新生成。</p>'
    document += '<div id="active">当前音轨：MVSep 背景 · Music＋SFX</div><audio id="player" controls preload="metadata" src="review/mvsep_background.wav"></audio><nav><button data-start="0" data-end="60" class="selected">完整 60 秒</button>'+buttons+'<button id="stop">全部暂停</button></nav><p id="window">当前试听窗口：0–60 秒。选窗口后，点击要听的音轨播放；切换音轨会暂停上一条。</p><section>'+cards+'</section><p>候选反应短窗不是人工标注的纯笑声真值。技术校验通过不等于声音质量验收，请以实际试听判断。</p></main>'
    document += '''<script>const player=document.querySelector('#player');let a=0,b=60;document.querySelectorAll('[data-start]').forEach(button=>button.onclick=()=>{player.pause();a=+button.dataset.start;b=+button.dataset.end;document.querySelectorAll('[data-start]').forEach(x=>x.classList.toggle('selected',x===button));document.querySelector('#window').textContent=`当前试听窗口：${a}–${b} 秒。点击要听的音轨播放。`});document.querySelector('#stop').onclick=()=>player.pause();document.querySelectorAll('.track').forEach(button=>button.onclick=()=>{player.pause();document.querySelector('#active').textContent='当前音轨：'+button.dataset.title;const play=()=>{player.currentTime=a;player.play().catch(()=>{});};if(player.getAttribute('src')===button.dataset.src&&player.readyState>=1){play()}else{player.onloadedmetadata=()=>{player.onloadedmetadata=null;play()};player.src=button.dataset.src;player.load()}});player.onplay=()=>{if(player.currentTime<a||player.currentTime>=b)player.currentTime=a};player.ontimeupdate=()=>{if(player.currentTime>=b)player.pause()};</script></html>'''
    (out/'index.html').write_text(document)
    print(json.dumps(dict(validated_files=len(validation), playback_gain=gain, summary=summary),ensure_ascii=False))


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('baseline',type=Path)
    args=ap.parse_args();main(args.output,args.baseline)
