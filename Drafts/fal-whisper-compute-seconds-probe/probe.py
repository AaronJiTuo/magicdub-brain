#!/usr/bin/env python3
"""Probe fal-ai/whisper: does any surface expose compute seconds for billing?"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import httpx

QUEUE_BASE = "https://queue.fal.run"
API_BASE = "https://api.fal.ai"
ENDPOINT = "fal-ai/whisper"
# Public sample used in fal docs (short conversation).
SAMPLE_URL = (
    "https://storage.googleapis.com/falserverless/model_tests/whisper/dinner_conversation.mp3"
)
OUT = Path(__file__).resolve().parent / "out"
POLL_INTERVAL_S = 2.0
POLL_DEADLINE_S = 300.0


def load_api_key() -> str:
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


def interesting_headers(h: httpx.Headers) -> dict[str, str]:
    keep = {}
    for k, v in h.items():
        lk = k.lower()
        if any(
            x in lk
            for x in (
                "fal",
                "bill",
                "cost",
                "unit",
                "price",
                "request",
                "meter",
                "usage",
                "comput",
            )
        ):
            keep[k] = v
    return keep


def walk_keys(obj, prefix="") -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            found.append(path)
            found.extend(walk_keys(v, path))
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
        found.extend(walk_keys(obj[0], f"{prefix}[]"))
    return found


def timing_like_paths(obj) -> dict:
    out = {}
    for path in walk_keys(obj):
        low = path.lower()
        if any(
            x in low
            for x in (
                "time",
                "comput",
                "bill",
                "cost",
                "metric",
                "unit",
                "duration",
                "second",
                "infer",
            )
        ):
            # resolve value
            cur = obj
            for part in path.replace("[]", ".0").split("."):
                if part == "0":
                    cur = cur[0]
                else:
                    cur = cur[part]
            if not isinstance(cur, (dict, list)):
                out[path] = cur
    return out


def run_once(client: httpx.Client, api_key: str, *, diarize: bool) -> dict:
    payload = {
        "audio_url": SAMPLE_URL,
        "task": "transcribe",
        "language": "es",
        "chunk_level": "segment",
        "diarize": diarize,
        "batch_size": 64,
        "prompt": "",
        "num_speakers": None,
    }
    submit = client.post(f"{QUEUE_BASE}/{ENDPOINT}", headers=headers(api_key), json=payload)
    submit.raise_for_status()
    body = submit.json()
    request_id = body["request_id"]
    status_url = body["status_url"]
    response_url = body["response_url"]

    deadline = time.time() + POLL_DEADLINE_S
    last_status = None
    last_status_headers: dict[str, str] = {}
    billable_units = None
    while time.time() < deadline:
        st = client.get(status_url, headers=headers(api_key))
        st.raise_for_status()
        last_status_headers = interesting_headers(st.headers)
        units = st.headers.get("x-fal-billable-units")
        if units is not None:
            try:
                billable_units = float(units)
            except ValueError:
                billable_units = units
        last_status = st.json()
        status = last_status.get("status")
        if status == "COMPLETED":
            break
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"job {status}: {last_status}")
        time.sleep(POLL_INTERVAL_S)
    else:
        raise RuntimeError("poll timed out")

    resp = client.get(response_url, headers=headers(api_key))
    resp.raise_for_status()
    result = resp.json()
    if isinstance(result, dict) and isinstance(result.get("data"), dict):
        result = result["data"]

    billing = client.get(
        f"{API_BASE}/v1/models/billing-events",
        headers=headers(api_key),
        params={"request_id": request_id},
    )
    billing_payload = None
    try:
        billing_payload = billing.json()
    except Exception:
        billing_payload = {"raw": billing.text[:500]}

    return {
        "diarize": diarize,
        "request_id": request_id,
        "result_top_level_keys": sorted(result.keys()) if isinstance(result, dict) else type(result).__name__,
        "result_timing_like_fields": timing_like_paths(result) if isinstance(result, dict) else {},
        "status_top_level_keys": sorted(last_status.keys()) if last_status else None,
        "status_metrics": (last_status or {}).get("metrics"),
        "status_timing_like_fields": timing_like_paths(last_status) if last_status else {},
        "status_interesting_headers": last_status_headers,
        "result_interesting_headers": interesting_headers(resp.headers),
        "x_fal_billable_units": billable_units,
        "billing_events_http": billing.status_code,
        "billing_events": billing_payload,
        "result_text_preview": (result.get("text") or "")[:120] if isinstance(result, dict) else None,
        "chunk_count": len(result.get("chunks") or []) if isinstance(result, dict) else None,
        "diarization_segment_count": len(result.get("diarization_segments") or [])
        if isinstance(result, dict)
        else None,
    }


def main() -> None:
    api_key = load_api_key()
    os.environ["FAL_KEY"] = api_key
    OUT.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=httpx.Timeout(30.0, read=120.0)) as client:
        pricing = client.get(
            f"{API_BASE}/v1/models/pricing",
            headers=headers(api_key),
            params={"endpoint_id": ENDPOINT},
        )
        pricing_json = pricing.json() if pricing.status_code == 200 else {"http": pricing.status_code, "body": pricing.text[:1000]}
        (OUT / "pricing.json").write_text(json.dumps(pricing_json, indent=2, ensure_ascii=False), encoding="utf-8")

        runs = []
        for diarize in (False, True):
            print(f"running whisper diarize={diarize} …", flush=True)
            info = run_once(client, api_key, diarize=diarize)
            runs.append(info)
            (OUT / f"run_diarize_{str(diarize).lower()}.json").write_text(
                json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(
                f"  keys={info['result_top_level_keys']} metrics={info['status_metrics']} "
                f"billable={info['x_fal_billable_units']}",
                flush=True,
            )

    summary = {
        "endpoint": ENDPOINT,
        "sample_url": SAMPLE_URL,
        "pricing": pricing_json,
        "runs": runs,
        "conclusions_draft": {
            "result_has_compute_seconds_field": any(
                "comput" in k.lower() or k.lower().endswith("seconds")
                for r in runs
                for k in (r.get("result_timing_like_fields") or {})
            ),
            "status_has_inference_time": all(
                isinstance((r.get("status_metrics") or {}).get("inference_time"), (int, float))
                for r in runs
            ),
            "billable_units_header_present": any(r.get("x_fal_billable_units") is not None for r in runs),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["conclusions_draft"], indent=2))


if __name__ == "__main__":
    main()
