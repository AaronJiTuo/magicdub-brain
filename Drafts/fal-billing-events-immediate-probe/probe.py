#!/usr/bin/env python3
"""Re-run IndexTTS2 for each sentence; query billing-events immediately after each TTS."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import fal_client
import httpx

QUEUE_BASE = "https://queue.fal.run"
API_BASE = "https://api.fal.ai"
ENDPOINT = "fal-ai/index-tts-2/text-to-speech"
POLL_INTERVAL_S = 2.0
POLL_DEADLINE_S = 600.0
# After TTS completes: try billing at these delays (seconds). 0 = immediate.
BILLING_RETRY_DELAYS_S = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)


def load_api_key_from_credentials() -> str:
    path = Path.home() / ".magicdub" / "cli" / "credentials"
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "FAL_KEY" and value.strip():
            return value.strip().strip('"').strip("'")
    raise SystemExit("FAL_KEY missing in ~/.magicdub/cli/credentials")


def headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Fal-No-Retry": "1",
        "x-app-fal-disable-fallback": "true",
    }


def run_tts(
    *,
    api_key: str,
    reference_path: Path,
    text: str,
    download_to: Path,
) -> tuple[str, float, float | None]:
    """Return (request_id, tts_elapsed_s, billable_units_or_none)."""
    os.environ["FAL_KEY"] = api_key
    audio_url = fal_client.upload_file(str(reference_path))
    payload = {
        "audio_url": audio_url,
        "emotional_audio_url": audio_url,
        "prompt": text,
    }
    t0 = time.perf_counter()
    with httpx.Client(timeout=httpx.Timeout(30.0, read=120.0)) as client:
        submit = client.post(
            f"{QUEUE_BASE}/{ENDPOINT}",
            headers=headers(api_key),
            json=payload,
        )
        submit.raise_for_status()
        body = submit.json()
        request_id = body["request_id"]
        status_url = body["status_url"]
        response_url = body["response_url"]

        billable_units: float | None = None
        deadline = time.time() + POLL_DEADLINE_S
        while time.time() < deadline:
            st = client.get(status_url, headers=headers(api_key))
            units_hdr = st.headers.get("x-fal-billable-units")
            if units_hdr:
                try:
                    billable_units = float(units_hdr)
                except ValueError:
                    pass
            st.raise_for_status()
            status = st.json().get("status")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"tts {status}: {st.text[:500]}")
            time.sleep(POLL_INTERVAL_S)
        else:
            raise TimeoutError(f"tts poll timed out request_id={request_id}")

        resp = client.get(response_url, headers=headers(api_key))
        resp.raise_for_status()
        result = resp.json()
        if isinstance(result, dict) and isinstance(result.get("data"), dict):
            result = result["data"]
        audio = result.get("audio") if isinstance(result, dict) else None
        url = audio.get("url") if isinstance(audio, dict) else None
        if not url:
            raise RuntimeError(f"no audio url: {result!r}"[:500])
        download_to.parent.mkdir(parents=True, exist_ok=True)
        with client.stream("GET", url) as stream:
            stream.raise_for_status()
            tmp = download_to.with_suffix(download_to.suffix + ".download")
            with tmp.open("wb") as f:
                for chunk in stream.iter_bytes():
                    f.write(chunk)
            tmp.replace(download_to)
    elapsed = time.perf_counter() - t0
    return request_id, elapsed, billable_units


def query_billing(
    *,
    admin_key: str,
    request_id: str,
) -> dict:
    t0 = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{API_BASE}/v1/models/billing-events",
            headers=headers(admin_key),
            params={"request_id": request_id, "limit": 10},
        )
    latency_ms = (time.perf_counter() - t0) * 1000.0
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text[:1000]}
    events = []
    if isinstance(data, dict):
        events = data.get("billing_events") or data.get("items") or data.get("data") or []
        if not isinstance(events, list):
            events = []
    summary_events = []
    for e in events:
        if not isinstance(e, dict):
            continue
        summary_events.append(
            {
                "request_id": e.get("request_id"),
                "endpoint_id": e.get("endpoint_id"),
                "timestamp": e.get("timestamp"),
                "output_units": e.get("output_units"),
                "unit_price": e.get("unit_price"),
                "percent_discount": e.get("percent_discount"),
                "cost_subtotal": e.get("cost_subtotal"),
                "cost_discount": e.get("cost_discount"),
                "cost_total": e.get("cost_total"),
                "cost_estimate_nano_usd": e.get("cost_estimate_nano_usd"),
            }
        )
    return {
        "http_status": r.status_code,
        "latency_ms": round(latency_ms, 1),
        "event_count": len(summary_events),
        "events": summary_events,
        "error": (data.get("error") if isinstance(data, dict) else None),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task",
        type=Path,
        default=Path.home()
        / "Movies/MagicDub/cli/youtube-SwQPurSL7HI_20260924_114857",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    parser.add_argument("--limit", type=int, default=22)
    args = parser.parse_args()

    admin_key = (os.environ.get("FAL_ADMIN_KEY") or "").strip()
    if not admin_key:
        raise SystemExit("set FAL_ADMIN_KEY in the environment (do not commit it)")

    model_key = load_api_key_from_credentials()
    task: Path = args.task.expanduser()
    state = json.loads((task / "state.json").read_text(encoding="utf-8"))
    sentences = state["assets"]["sentences"][: args.limit]

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "tmp_tts"
    work.mkdir(exist_ok=True)
    results_path = out_dir / "results.jsonl"
    if results_path.exists():
        results_path.unlink()

    immediate_hits = 0
    first_hit_delays: list[float] = []

    print(f"task={task} sentences={len(sentences)}", flush=True)
    for sent in sentences:
        sid = int(sent["id"])
        src = (sent.get("src") or {}).get("audio") or {}
        ref = task / src["path"]
        tgt = next(
            (t for t in sent.get("tgt") or [] if t.get("attempt") == 1 and t.get("text")),
            None,
        )
        if not tgt:
            print(f"skip {sid}: no attempt-1 text", flush=True)
            continue
        text = str(tgt["text"])
        print(f"\n→ sentence {sid} TTS…", flush=True)
        request_id, tts_s, units = run_tts(
            api_key=model_key,
            reference_path=ref,
            text=text,
            download_to=work / f"{sid}.wav",
        )
        print(f"  request_id={request_id} tts={tts_s:.1f}s units={units}", flush=True)

        billing_tries: list[dict] = []
        hit_delay: float | None = None
        t_done = time.perf_counter()
        for delay in BILLING_RETRY_DELAYS_S:
            target = t_done + delay
            now = time.perf_counter()
            if target > now:
                time.sleep(target - now)
            waited = time.perf_counter() - t_done
            q = query_billing(admin_key=admin_key, request_id=request_id)
            q["delay_s"] = round(waited, 3)
            billing_tries.append(q)
            print(
                f"  billing @{q['delay_s']:.3f}s status={q['http_status']} "
                f"events={q['event_count']} cost_total="
                f"{(q['events'][0].get('cost_total') if q['events'] else None)!r}",
                flush=True,
            )
            if q["http_status"] == 200 and q["event_count"] > 0 and hit_delay is None:
                hit_delay = q["delay_s"]
                if delay == 0.0:
                    immediate_hits += 1
                break

        if hit_delay is not None:
            first_hit_delays.append(hit_delay)

        row = {
            "sentence_id": sid,
            "request_id": request_id,
            "tts_elapsed_s": round(tts_s, 3),
            "billable_units_header": units,
            "billing_tries": billing_tries,
            "first_hit_delay_s": hit_delay,
            "immediate_hit": bool(billing_tries and billing_tries[0]["event_count"] > 0),
        }
        with results_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    n = max(len(first_hit_delays), 1)
    summary = {
        "sentences_tested": len(list(results_path.read_text().splitlines()))
        if results_path.exists()
        else 0,
        "immediate_hits": immediate_hits,
        "eventual_hits": len(first_hit_delays),
        "first_hit_delays_s": first_hit_delays,
        "avg_first_hit_delay_s": round(sum(first_hit_delays) / n, 3)
        if first_hit_delays
        else None,
        "max_first_hit_delay_s": max(first_hit_delays) if first_hit_delays else None,
        "never_found": (results_path.read_text().count("\n") if results_path.exists() else 0)
        - len(first_hit_delays),
    }
    # recount never_found properly
    rows = [
        json.loads(line)
        for line in results_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary["sentences_tested"] = len(rows)
    summary["immediate_hits"] = sum(1 for r in rows if r.get("immediate_hit"))
    summary["eventual_hits"] = sum(1 for r in rows if r.get("first_hit_delay_s") is not None)
    summary["never_found"] = sum(1 for r in rows if r.get("first_hit_delay_s") is None)
    delays = [r["first_hit_delay_s"] for r in rows if r.get("first_hit_delay_s") is not None]
    summary["first_hit_delays_s"] = delays
    summary["avg_first_hit_delay_s"] = round(sum(delays) / len(delays), 3) if delays else None
    summary["max_first_hit_delay_s"] = max(delays) if delays else None

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md = [
        "# fal billing-events 即时性探测结果",
        "",
        f"- 任务：`{task}`",
        f"- 测试句数：{summary['sentences_tested']}",
        f"- **即时命中**（delay=0 且有 event）：{summary['immediate_hits']}",
        f"- 最终命中（≤10s 重试内）：{summary['eventual_hits']}",
        f"- 始终未命中：{summary['never_found']}",
        f"- 首次命中延迟 avg/max（秒）："
        f"{summary['avg_first_hit_delay_s']} / {summary['max_first_hit_delay_s']}",
        "",
        "明细见 `results.jsonl`。",
        "",
    ]
    (out_dir / "SUMMARY.md").write_text("\n".join(md), encoding="utf-8")
    print("\n" + "\n".join(md), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
