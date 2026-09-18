"""Render a local listening comparison from completed experiment artifacts."""
import html
import json
import sys
from pathlib import Path


def render(out):
    m=json.loads((out/'manifest.json').read_text()); cards=[]; results=[]
    esc=html.escape
    for c in m['cases']:
        p=out/'samples'/c['case_id']/'result.json'
        r=json.loads(p.read_text()) if p.exists() else {'status':'not_run'}
        results.append(r)
        d=c['reference']['duration']; f=r.get('audio',{}).get('duration')
        def audio(label,url,duration):
            return f'<div class="player"><label>{label} <span>{duration:.3f} 秒</span></label><audio controls preload="metadata" src="{esc(url)}"></audio></div>'
        players=audio('A · 原声参考',c['source_relative'],d)+audio('B · 已有 IndexTTS 2',c['index_relative'],c['index']['duration'])
        players+=audio('C · Fish S2.1 Pro',c['fish_relative'],f) if f else '<div class="player"><label>C · Fish</label><p>'+esc(r.get('error',r['status']))+'</p></div>'
        ratio=f/d if f else None
        ratio_text=f'Fish / 原句时长 {ratio:.2f} 倍' if ratio else r['status']
        cards.append(f'''<article data-short="{str(d<.5).lower()}"><header><div><span class="num">{c['case_id'][:2]}</span><strong>{esc(c['translated_text'])}</strong></div><span class="badge {'short' if d<.5 else ''}">{'超短参考 · ' if d<.5 else ''}{d:.2f} 秒</span></header><p class="source">{esc(c['source_text'])}</p><p class="meta">{esc(c['project'])} · {esc(c['segment_id'])} · {c['start_ms']/1000:.3f}s · {esc(str(c['speaker']))}</p><div class="players">{players}</div><footer><button class="sequence">按 A → B → C 连听</button><span>{ratio_text}</span></footer></article>''')
    success=sum(r['status']=='generated' and r.get('decode_ok',False) for r in results)
    byte_count=sum(c['target_utf8_bytes'] for c,r in zip(m['cases'],results) if r['status']=='generated')
    cost=byte_count*m['price_usd_per_million_utf8_bytes']/1e6*7
    summary={'model':m['model'],'success':success,'selected':len(results),'target_utf8_bytes_success':byte_count,'calculated_cost_cny':cost,'cases':results}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    document='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fish S2.1 Pro · MagicDub 试听对照</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f5f3;color:#172b2a;font:15px/1.55 system-ui,-apple-system,sans-serif}main{max-width:1120px;margin:auto;padding:44px 24px}.eyebrow{color:#33716a;font-weight:700;letter-spacing:.12em;font-size:12px}h1{font-size:34px;margin:6px 0 12px}p{margin:10px 0}.intro{max-width:900px;color:#536461}.summary{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.stat{padding:12px 18px;background:white;border-radius:12px;border:1px solid #dce4df}.toolbar{display:flex;gap:8px;align-items:center;margin:24px 0}button{border:1px solid #abc9bf;background:white;border-radius:8px;padding:9px 14px;color:#21594a;cursor:pointer}button.active{background:#21594a;color:white}article{background:white;border:1px solid #dce4df;border-radius:16px;padding:22px;margin:16px 0}header{display:flex;align-items:start;justify-content:space-between;gap:20px}header strong{font-size:19px}.num{display:inline-block;color:#569282;font-weight:750;margin-right:12px}.badge{white-space:nowrap;border-radius:99px;padding:4px 10px;background:#eff3f0;font-size:12px}.short{background:#fff0d6;color:#94610f}.source{color:#61706b;margin-top:15px}.meta{font-size:12px;color:#87928e;overflow-wrap:anywhere}.players{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:20px 0 16px}.player{background:#f7f9f7;border-radius:10px;padding:12px;min-width:0}.player label{display:block;font-size:13px;font-weight:600;margin-bottom:10px}.player span{float:right;color:#74817b;font-weight:400}audio{width:100%;height:38px}footer{display:flex;align-items:center;justify-content:space-between;gap:10px;color:#718079;font-size:12px}.notice{border-left:3px solid #c6a55b;padding-left:14px;color:#73664b}article[hidden]{display:none}@media(max-width:750px){main{padding:24px 12px}h1{font-size:28px}.players{grid-template-columns:1fr}header{flex-direction:column;gap:8px}article{padding:16px}}
</style><main><div class="eyebrow">MAGICDUB / MODEL LISTENING TEST</div><h1>Fish S2.1 Pro 逐句试听</h1><p class="intro">同一句原声、相同的已有中文译文，比较原声参考、已有 IndexTTS 2 与本次 Fish Instant clone。先听 3 个不足 0.5 秒的极短参考，再听长句中的音色与语气。</p>'''
    document+=f'<div class="summary"><div class="stat">生成并完整解码 <b>{success} / {len(results)}</b></div><div class="stat">入口 <b>{esc(m["model"])}</b></div><div class="stat">本轮配音 ¥{cost:.6f}</div><div class="stat">超短参考 0.24 / 0.28 / 0.38 秒</div></div>'
    document+='<p class="notice">所有音频均为各自原始时长，未变速、裁切或后期响度匹配。Fish 使用原句未补长参考，不添加情绪标签；已有 IndexTTS 的这 3 个超短参考曾尾补静音到 0.6 秒。自动检查只验证文件、能量与完整解码，音色、情绪和正确朗读由试听判断。</p><div class="toolbar"><button class="filter active" data-filter="all">全部 12 句</button><button class="filter" data-filter="short">只听不足 0.5 秒</button><button id="stop">停止播放</button></div>'
    document+=''.join(cards)
    document+='''<p class="intro">本页和 WAV 均保存在同一实验目录，可离线打开 index.html。参考来自 2026-09-18 已完成案例。本轮未重新执行 ASR、翻译或分离，未替换 MagicDub 默认模型。</p></main><script>
let activeSequence=null;function stop(){activeSequence=null;document.querySelectorAll('audio').forEach(a=>{a.pause();a.currentTime=0;a.onended=null});document.querySelectorAll('.sequence').forEach(b=>b.textContent='按 A → B → C 连听')}
document.querySelectorAll('audio').forEach(a=>a.addEventListener('play',()=>document.querySelectorAll('audio').forEach(b=>{if(b!==a)b.pause()})));
document.querySelectorAll('.sequence').forEach(b=>b.onclick=()=>{stop();let audios=[...b.closest('article').querySelectorAll('audio')];activeSequence=b;b.textContent='正在连听…';let i=0;function next(){if(activeSequence!==b)return;if(i===audios.length){stop();return}let a=audios[i++];a.currentTime=0;a.onended=()=>setTimeout(next,450);a.play().catch(()=>stop())}next()});
document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{stop();document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('article').forEach(a=>a.hidden=b.dataset.filter==='short'&&a.dataset.short!=='true')});document.querySelector('#stop').onclick=stop;
</script></html>'''
    (out/'index.html').write_text(document,encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='cases'},ensure_ascii=False))


if __name__=='__main__':render(Path(sys.argv[1]))
