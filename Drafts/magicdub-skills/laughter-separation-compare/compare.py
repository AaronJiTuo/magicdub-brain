"""Bounded, resumable fal separation experiment; never resubmit ambiguous requests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import fal_client
import requests
from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
ROOT = HERE / "runs/stevejobs-first60"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(p):
    return json.loads(p.read_text())


def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(p)


def headers(billing=False):
    values = dotenv_values(Path.home() / ".magicdub/credentials.env", interpolate=False)
    for k in ("FAL_KEY", "FAL_BILLING_KEY"):
        if values.get(k) and not os.environ.get(k):
            os.environ[k] = values[k]
    key = os.environ.get("FAL_BILLING_KEY") if billing else None
    return {"Authorization": "Key " + (key or os.environ["FAL_KEY"]),
            "X-Fal-No-Retry": "1", "x-app-fal-disable-fallback": "true"}


def get(url, **kw):
    for n in range(3):
        try:
            r = requests.get(url, timeout=(15, 60), **kw)
            if r.status_code not in (429, 500, 502, 503, 504):
                return r
        except requests.RequestException:
            if n == 2:
                raise RuntimeError("Read failed; resume saved request, do not resubmit") from None
        time.sleep(2 ** n)
    raise RuntimeError("Read temporarily unavailable; saved request retained")


def pricing():
    eps = ["fal-ai/demucs", "fal-ai/sam-audio/span-separate", "fal-ai/sam-audio/separate", "fal-ai/whisper",
           "fal-ai/deepfilternet3", "fal-ai/elevenlabs/audio-isolation"]
    r = get("https://api.fal.ai/v1/models/pricing", headers=headers(),
            params={"endpoint_id": ",".join(eps)})
    r.raise_for_status()
    result = r.json()
    write(ROOT / "pricing.json", {"checked_at": now(), "data": result})
    return {p["endpoint_id"]: p for p in result["prices"]}


def upload(name):
    f = ROOT / ("original-pcm24.wav" if name == "pcm24" else "original.wav")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    cache = ROOT / ("upload-pcm24.json" if name == "pcm24" else "upload.json")
    if cache.exists():
        old = read(cache)
        if old["sha256"] == sha and time.time() - old["time"] < 43200:
            return old["url"]
    headers()
    u = fal_client.upload_file(str(f))
    write(cache, {"sha256": sha, "url": u, "time": time.time()})
    return u


def experiment(name):
    config = read(ROOT / "experiment.json")
    if name in ("baseline1", "pcm24"):
        return "fal-ai/sam-audio/separate", {
            "prompt": "speech", "predict_spans": False, "reranking_candidates": 1,
            "acceleration": "balanced", "max_chunk_duration": 60, "chunk_overlap": 5,
            "output_format": "wav"}
    eps = "fal-ai/demucs" if name == "demucs" else "fal-ai/sam-audio/span-separate"
    params = dict(config["demucs"] if name == "demucs" else config["sam"])
    if name != "demucs":
        params["reranking_candidates"] = int(name[-1])
    return eps, params


def run(name):
    folder = ROOT / name
    folder.mkdir(exist_ok=True)
    state_file = folder / "attempt.json"
    endpoint, params = experiment(name)
    if (folder / "result.json").exists():
        print(name, "cached result", flush=True)
        return
    a = read(state_file) if state_file.exists() else {
        "name": name, "endpoint": endpoint, "parameters": params,
        "audio_duration_seconds": 60, "started_at": now(), "status": "prepared"}
    if a["endpoint"] != endpoint or a["parameters"] != params:
        raise RuntimeError("Configuration changed: use a separate run, never overwrite receipts")
    if not a.get("request_id"):
        if a["status"] != "prepared":
            raise RuntimeError("Submission may have occurred; investigate receipt before retry")
        payload = {"audio_url": upload(name), **params}
        write(folder / "input.json", payload)
        a.update(status="submitting", sent_at=now())
        write(state_file, a)
        try:
            r = requests.post("https://queue.fal.run/" + endpoint,
                              headers=headers(), json=payload, timeout=(15, 90))
        except requests.RequestException:
            a["status"] = "submission_unknown"
            write(state_file, a)
            raise RuntimeError("Submission unknown; will not repeat POST") from None
        try:
            body = r.json()
        except ValueError:
            body = {"http_status": r.status_code}
        write(folder / "submission.json", body)
        if r.status_code >= 400 or not body.get("request_id"):
            a.update(status="submission_failed_or_unknown", http_status=r.status_code)
            write(state_file, a)
            raise RuntimeError(f"Submission HTTP {r.status_code}")
        for k in ("response_url", "status_url"):
            u = urlparse(body[k])
            if u.scheme != "https" or u.hostname != "queue.fal.run":
                raise RuntimeError("Unexpected queue URL")
        a.update({k: body[k] for k in ("request_id", "response_url", "status_url")})
        a["status"] = "submitted"
        write(state_file, a)
        print(name, "submitted", a["request_id"], flush=True)
    last = None
    for _ in range(360):
        r = get(a["status_url"], headers=headers())
        r.raise_for_status()
        s = r.json()
        write(folder / "status.json", s)
        status = s.get("status")
        if status != last:
            print(name, status, flush=True)
            last = status
        a["status"] = status
        if s.get("metrics"):
            a["metrics"] = s["metrics"]
        write(state_file, a)
        if status == "COMPLETED":
            r = get(a["response_url"], headers=headers())
            a.update(finished_at=now(), result_http_status=r.status_code,
                     billable_units_header=r.headers.get("x-fal-billable-units"))
            body = r.json()
            if r.status_code >= 400:
                a["status"] = "failed"
                write(folder / "error.json", body)
                write(state_file, a)
                raise RuntimeError(f"Model failed HTTP {r.status_code}; not automatically retrying")
            if "data" in body:
                body = body["data"]
            write(folder / "result.json", body)
            a["status"] = "succeeded"
            write(state_file, a)
            print(name, "succeeded", "billable_units", a["billable_units_header"],
                  "metrics", a.get("metrics"), flush=True)
            return
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Terminal {status}; no automatic paid retry")
        time.sleep(5)
    raise RuntimeError("Remote request remains pending; resume the same name later")


def download(name):
    folder = ROOT / name
    result = read(folder / "result.json")
    for k in ("vocals",) if name == "demucs" else ("target", "residual"):
        path = folder / (k + ".wav")
        if path.exists():
            continue
        u = result[k]["url"]
        if urlparse(u).scheme != "https":
            raise RuntimeError("Expected HTTPS output URL")
        r = get(u)
        r.raise_for_status()
        temp = path.with_suffix(".download")
        temp.write_bytes(r.content)
        import soundfile as sf
        info = sf.info(temp)
        if info.duration <= 0:
            raise RuntimeError("Empty output")
        temp.replace(path)
        print(name, k, info.samplerate, info.channels, info.subtype, info.duration, flush=True)


def billing():
    prices = pricing()
    attempts = [p for p in ROOT.glob("*/attempt.json")]
    ids = [read(p).get("request_id") for p in attempts if read(p).get("request_id")]
    events = []
    status = None
    if ids:
        r = get("https://api.fal.ai/v1/models/billing-events", headers=headers(True),
                params={"request_id": ",".join(ids), "limit": 100})
        status = r.status_code
        if r.ok:
            events = r.json().get("billing_events", [])
    write(ROOT / "billing-events.json", {"checked_at": now(), "http_status": status,
                                         "billing_events": events})
    rows = []
    for path in attempts:
        a = read(path)
        p = prices[a["endpoint"]]
        matches = [e for e in events if e.get("request_id") == a.get("request_id")]
        units = a.get("billable_units_header")
        basis = "provider_billable_units_header"
        if matches:
            usd = sum((Decimal(str(e["cost_total"])) for e in matches), Decimal(0))
            cost_status = "confirmed"
            basis = "billing-events"
        else:
            if units is None and p["unit"] == "compute seconds":
                units = a.get("metrics", {}).get("inference_time")
                basis = "inference_time_estimate"
            if units is None and a["status"] == "succeeded":
                if a["endpoint"] in ("fal-ai/sam-audio/span-separate", "fal-ai/sam-audio/separate"):
                    out = read(path.parent / "result.json")
                    n = a["parameters"]["reranking_candidates"]
                    units = Decimal(str(out["duration"])) / 30 * (1 + Decimal("0.5") * (n - 1))
                    basis = "documented_output_duration_and_candidates_estimate"
                elif a["endpoint"] == "fal-ai/demucs" and p["unit"] == "seconds":
                    units = a["audio_duration_seconds"]
                    basis = "input_audio_seconds_estimate"
            usd = Decimal(str(units)) * Decimal(str(p["unit_price"])) if units is not None else None
            cost_status = "estimated" if usd is not None else "unknown"
        row = {"name": a["name"], "request_id": a.get("request_id"), "status": a["status"],
               "audio_duration_seconds": a["audio_duration_seconds"],
               "inference_time_seconds": a.get("metrics", {}).get("inference_time"),
               "billing_unit": p["unit"], "billed_quantity": str(units) if units is not None else None,
               "unit_price_usd": str(p["unit_price"]), "cost_usd": str(usd) if usd is not None else None,
               "cost_cny": str(usd * 7) if usd is not None else None,
               "cost_status": cost_status, "basis": basis}
        rows.append(row)
    total = sum((Decimal(r["cost_cny"]) for r in rows if r["cost_cny"] is not None), Decimal(0))
    report = {"checked_at": now(), "fx_usd_cny": 7, "rows": rows,
              "known_total_cny": str(total), "unknown_attempts": sum(r["cost_cny"] is None for r in rows),
              "billing_http_status": status}
    write(ROOT / "costs.json", report)
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["pricing", "run", "download", "billing"])
    parser.add_argument("name", nargs="?", choices=["demucs", "sam1", "sam3", "baseline1", "pcm24"])
    args = parser.parse_args()
    if args.action == "run":
        run(args.name)
    elif args.action == "download":
        download(args.name)
    elif args.action == "billing":
        billing()
    else:
        print(json.dumps(pricing()))
