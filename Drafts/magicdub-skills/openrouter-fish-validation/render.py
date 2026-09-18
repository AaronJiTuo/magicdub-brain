"""Build a portable listening comparison from preserved, unmodified outputs."""
import argparse
import html
import json
import shutil
from pathlib import Path


def render(out, baseline):
    manifest = json.loads((baseline/'manifest.json').read_text())
    receipts = [json.loads(p.read_text()) for p in sorted((out/'requests').glob('*/receipt.json'))]
    rows = {r['id']:r for r in receipts}
    selected = ['05_HC4lPDHT15A_s0000','09_qmMIk13HOLQ_s0000','11_uDCm_s0000','01_HC4lPDHT15A_s0001','07_qmMIk13HOLQ_s0067','10_uDCm_s0019']
    cards = []
    def player(label, path, duration=None):
        sub = f'{duration:.3f} 秒' if duration is not None else ''
        return f'<div class="player"><b>{html.escape(label)}</b><small>{sub}</small><audio controls preload="metadata" src="{html.escape(path)}"></audio></div>'
    for sid in selected:
        c = next(c for c in manifest['cases'] if c['case_id']==sid)
        local = out/'baseline'/sid
        local.mkdir(parents=True,exist_ok=True)
        media = []
        for name,label,field in [('source.wav','英文原声','source_relative'),('index.wav','IndexTTS · 原有结果','index_relative'),('fish.wav','Fish 官方 Free · 原有结果','fish_relative')]:
            shutil.copy2(baseline/c[field],local/name)
            media.append(player(label,str((local/name).relative_to(out))))
        for model,label in [('free','OpenRouter · Free'),('paid','OpenRouter · Pro')]:
            rid = model+('-baseline' if sid==selected[0] else '-'+sid)
            r = rows[rid]
            media.append(player(label,'requests/'+rid+'/output.mp3',r['audio']['duration']))
        cards.append(f'<article data-short="{str(c["reference"]["duration"]<.5).lower()}"><div class="row"><span class="tag">参考 {c["reference"]["duration"]:.2f} 秒</span><small>{html.escape(sid)}</small></div><h2>{html.escape(c["translated_text"])}</h2><p class="source">{html.escape(c["source_text"])}</p><div class="players">'+''.join(media)+'</div></article>')
    extras=[]
    baseline_ids={m+('-baseline' if sid==selected[0] else '-'+sid) for m in ['free','paid'] for sid in selected}
    for r in receipts:
        if r['id'] in baseline_ids or r['status']!='generated':continue
        path=out/'requests'/r['id']
        audio=path/'output.mp3'
        if not audio.exists():audio=path/'output.wav'
        if audio.exists():extras.append(player(r['id'],str(audio.relative_to(out)),r.get('audio',{}).get('duration')))
    successful=sum(r['status']=='generated' for r in receipts)
    summary={'requests':len(receipts),'generated':successful,'rejected':sum(r['status']=='rejected' for r in receipts),'baseline_requests':12,'baseline_cases':6,'receipts':receipts}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenRouter × Fish｜API 实测与试听</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f3f5f9;color:#172338;font:16px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1420px;margin:auto;padding:46px 30px 80px}header{padding:20px 0 26px}.eyebrow{font-size:13px;letter-spacing:2px;color:#5265a4}h1{font-size:34px;line-height:1.3;margin:12px 0}header p{max-width:950px;color:#586477}.stats{display:flex;gap:12px;flex-wrap:wrap}.stat{background:white;padding:13px 20px;border:1px solid #dce3ee;border-radius:12px}.stat strong{color:#374d93}article,.panel{background:#fff;border:1px solid #dde3ec;border-radius:18px;padding:24px;margin:20px 0;box-shadow:0 4px 22px #12233805}.row{display:flex;gap:14px;align-items:center;flex-wrap:wrap}.tag{background:#edf0ff;border-radius:6px;color:#4b51a2;font-size:13px;padding:3px 9px}small{color:#798394;font-size:12px}h2{font-size:21px;line-height:1.5;margin:18px 0 8px}.source{color:#6b7280;margin:0 0 20px}.players{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px}.player{padding:14px 11px;background:#f6f8fc;border-radius:10px;min-width:0}.player b{display:block;font-size:13px;line-height:1.5;min-height:39px}.player small{display:block;min-height:20px}audio{width:100%;height:38px;margin-top:8px}button,a.button{display:inline-block;background:#fff;color:#304774;border:1px solid #c8d2e2;border-radius:8px;padding:9px 16px;font:inherit;cursor:pointer;text-decoration:none}button.active{background:#344c87;color:white}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}.extra{grid-template-columns:repeat(4,minmax(0,1fr))}@media(max-width:1000px){.players{grid-template-columns:repeat(2,minmax(0,1fr))}.extra{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){main{padding:24px 14px}h1{font-size:27px}.players,.extra{grid-template-columns:1fr}article{padding:18px}}
    </style><main><header><div class="eyebrow">MAGICDUB / 2026.09.19 / API VALIDATION</div><h1>OpenRouter × Fish S2.1 Pro</h1><p>同一原声、原文和中文译文，比较官方 Fish、IndexTTS 与 OpenRouter 两个入口。核心逐句克隆已跑通；接口能力并不完全相同。</p><div class="stats"><div class="stat"><strong>12 / 12</strong> 基础克隆成功</div><div class="stat"><strong>0.24 / 0.28 / 0.38 秒</strong> 未补长参考</div><div class="stat"><strong>MP3 + PCM</strong> 真实输出</div></div><p>试听关注：中文发音、音色、原句语气和完整朗读。旧结果生成于前一日，输出格式与参数不同，这不是严格受控的模型音质排名；接口成功也不代表中文口音已改善。</p><div class="actions"><button class="active" data-filter="all">全部 6 句</button><button data-filter="short">只听不足 0.5 秒参考</button><a class="button" href="report.md">完整测试报告</a><a class="button" href="summary.json">脱敏测试数据</a></div></header>'''+''.join(cards)+('<section class="panel"><h2>补充能力测试输出</h2><p>名称包含 pcm、options 或 emotion；参数与结果见报告。这些不纳入上面的基础对照。</p><div class="players extra">'+''.join(extras)+'</div></section>' if extras else '')+'''<p>保留全部原始响应和失败凭据。音频没有进行时间拉伸、裁剪或重新合成；PCM 仅添加 WAV 容器。</p></main><script>document.querySelectorAll('button[data-filter]').forEach(b=>b.onclick=()=>{document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter==='short'&&a.dataset.short!=='true');document.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===b))});document.addEventListener('play',e=>{if(e.target.tagName==='AUDIO')document.querySelectorAll('audio').forEach(a=>{if(a!==e.target)a.pause()})},true)</script></html>'''
    (out/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='receipts'}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);a=p.parse_args();render(a.output,a.baseline)
