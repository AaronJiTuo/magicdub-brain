"""One fixed, resumable Qwen ASR experiment; never resubmit an uncertain task."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MODEL = "qwen-audio-3.0-asr-flash-filetrans"
SHA256 = "df6d7f72173914e90757d66c4185ebcaca2eff432b7ec6217737f60e8465366e"
ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / "private"


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(args):
    import requests
    from magicdub.config import beijing_base, credentials, dashscope_base
    from magicdub.uploads import bailian_upload

    source = Path(args.source).expanduser().resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SHA256:
        raise ValueError("The source must match the prior Fun-ASR fixture")
    with wave.open(str(source)) as stream:
        fmt = {"sample_rate": stream.getframerate(), "channels": stream.getnchannels(),
               "sample_width": stream.getsampwidth(), "frames": stream.getnframes()}
    if fmt != {"sample_rate": 16000, "channels": 1, "sample_width": 2, "frames": 512000}:
        raise ValueError("Unexpected audio format")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(source),
                    "-f", "null", "-"], check=True, capture_output=True)
    if (ROOT / "summary.json").exists() and load(ROOT / "summary.json").get("status") == "succeeded":
        print(json.dumps({"status": "cached_success", "network_calls": 0}), flush=True)
        return
    credentials()
    key = os.environ.get("DASHSCOPE_API_KEY")
    base = dashscope_base()
    if not key or not beijing_base(base):
        raise ValueError("A configured Beijing API key and base are required")
    base_hash = hashlib.sha256(base.encode()).hexdigest()
    state_path = PRIVATE / "state.json"
    if state_path.exists():
        state = load(state_path)
        if state["base_sha256"] != base_hash or state["source_sha256"] != digest:
            raise ValueError("Cannot resume against a different input or workspace")
    else:
        state = {"model": MODEL, "source_sha256": digest, "base_sha256": base_hash,
                 "created_at": datetime.now(timezone.utc).isoformat(), "requests": []}
        save(state_path, state)

    original_get, original_post = requests.get, requests.post

    def tracked(method, url, **kwargs):
        parsed = urlparse(url)
        role = ("asr_submit" if parsed.path.endswith("/transcription") else
                "upload_policy" if parsed.path.endswith("/uploads") else
                "poll" if "/tasks/" in parsed.path else
                "audio_upload" if method == "POST" else "result_download")
        entry = {"method": method, "role": role, "status": "sending", "started": time.time()}
        state["requests"].append(entry)
        save(state_path, state)
        fn = original_get if method == "GET" else original_post
        response = fn(url, **kwargs)
        entry.update(status=response.status_code, elapsed_seconds=round(time.time() - entry["started"], 3))
        save(state_path, state)
        return response

    requests.get = lambda url, **kw: tracked("GET", url, **kw)
    requests.post = lambda url, **kw: tracked("POST", url, **kw)
    headers = {"Authorization": "Bearer " + key}
    parameters = {"diarization_enabled": True, "special_word_filter": json.dumps(
        {"filter_with_signed": {"word_list": ["肏屄"]}, "system_reserved_filter": False},
        ensure_ascii=False), "language_hints": ["en"]}
    if not state.get("task_id"):
        if state.get("submission_started"):
            print(json.dumps({"status": "submission_already_attempted", "resubmitted": False}), flush=True)
            return
        if not state.get("audio_url"):
            state["audio_url"] = bailian_upload(source, base=base, endpoint=MODEL, api_key=key)
            save(state_path, state)
        state["submission_started"] = time.time()
        save(state_path, state)
        response = requests.post(base + "/services/audio/asr/transcription", headers={
            **headers, "Content-Type": "application/json", "X-DashScope-Async": "enable",
            "X-DashScope-OssResourceResolve": "enable"},
            json={"model": MODEL, "input": {"file_urls": [state["audio_url"]]},
                  "parameters": parameters}, timeout=(15, 90), allow_redirects=False)
        body = response.json()
        save(PRIVATE / "submission.json", body)
        state["task_id"] = body.get("output", {}).get("task_id")
        save(state_path, state)
        if response.status_code != 200 or not state["task_id"]:
            public = {"status": "submission_failed", "http_status": response.status_code,
                      "code": body.get("code"), "request_id": body.get("request_id"),
                      "model": MODEL, "source_sha256": digest, "requests": state["requests"],
                      "billing_status": "unreconciled"}
            save(ROOT / "summary.json", public)
            print(json.dumps(public), flush=True)
            return
        print(json.dumps({"status": "submitted", "task_id": state["task_id"]}), flush=True)

    deadline = time.monotonic() + 1200
    while True:
        if (PRIVATE / "task.json").exists():
            task = load(PRIVATE / "task.json")
        else:
            task = {}
        if task.get("output", {}).get("task_status") not in ("SUCCEEDED", "FAILED", "CANCELED"):
            response = requests.get(base + "/tasks/" + state["task_id"], headers=headers,
                                    timeout=(15, 90), allow_redirects=False)
            if response.status_code != 200:
                raise ValueError("Polling HTTP failure; rerun to resume same task")
            task = response.json()
            save(PRIVATE / "task.json", task)
        status = task.get("output", {}).get("task_status")
        print(json.dumps({"status": status, "task_id": state["task_id"]}), flush=True)
        if status in ("SUCCEEDED", "FAILED", "CANCELED"):
            break
        if time.monotonic() >= deadline:
            print('{"status":"poll_timeout_resume_same_task"}', flush=True)
            return
        time.sleep(5)

    result = task.get("output", {}).get("results", [{}])[0]
    public = {"status": "task_failed", "model": MODEL, "task_id": state["task_id"],
              "task_status": status, "subtask_status": result.get("subtask_status"),
              "parameters": parameters, "source_sha256": digest, "audio": {**fmt, "seconds": 32.0},
              "base": "workspace-beijing" if "maas" in base else "public-beijing",
              "usage": task.get("usage"), "requests": state["requests"],
              "billing_status": "unreconciled"}
    if status != "SUCCEEDED" or result.get("subtask_status") != "SUCCEEDED":
        public["error_code"] = result.get("code", task.get("code"))
        save(ROOT / "summary.json", public)
        print(json.dumps(public), flush=True)
        return
    if (PRIVATE / "transcription.json").exists():
        raw = load(PRIVATE / "transcription.json")
    else:
        parsed = urlparse(result["transcription_url"])
        if (parsed.scheme != "https" or not (parsed.hostname or "").endswith(".aliyuncs.com")
                or parsed.username or parsed.password or parsed.port not in (None, 443)):
            raise ValueError("Unexpected transcription result host")
        response = requests.get(result["transcription_url"], timeout=(15, 90), allow_redirects=False)
        if response.status_code != 200:
            raise ValueError("Result download failed; resume the saved task")
        raw = response.json()
        save(PRIVATE / "transcription.json", raw)
    sentences = [sentence for channel in raw.get("transcripts", []) for sentence in channel.get("sentences", [])]
    save(ROOT / "provider_transcript.json", {"properties": raw.get("properties"),
                                            "transcripts": raw.get("transcripts")})
    valid = bool(sentences) and all(
        isinstance(s.get("begin_time"), (int, float)) and isinstance(s.get("end_time"), (int, float))
        and 0 <= s["begin_time"] < s["end_time"] <= 32050 and s.get("text", "").strip()
        and s.get("speaker_id") is not None for s in sentences)
    transcript = [{"start": s.get("begin_time", 0) / 1000, "end": s.get("end_time", 0) / 1000,
                   "speaker": s.get("speaker_id"), "text": s.get("text")} for s in sentences]
    save(ROOT / "transcript.json", {"model": MODEL, "segments": transcript})
    duration = (task.get("usage") or {}).get("duration")
    public.update(status="succeeded" if valid else "invalid_transcript", sentences=len(sentences),
                  speaker_ids=sorted({str(s.get("speaker_id")) for s in sentences}),
                  timestamps_and_speakers_valid=valid, properties=raw.get("properties"),
                  source_unchanged=hashlib.sha256(source.read_bytes()).hexdigest() == digest,
                  submission_to_result_seconds=round(time.time() - state["submission_started"], 3),
                  requests=state["requests"], estimated_cny=round(duration * 0.00022, 6)
                  if isinstance(duration, (int, float)) else None,
                  billing_status="estimated_not_reconciled" if isinstance(duration, (int, float)) else "unreconciled",
                  unit_price_cny_per_second=0.00022)
    save(ROOT / "summary.json", public)
    print(json.dumps(public, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(args.runtime).expanduser().resolve() / "src"))
    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    from filelock import FileLock
    with FileLock(str(PRIVATE / "run.lock"), timeout=0):
        try:
            main(args)
        except Exception as exc:
            print(json.dumps({"status": "stopped_preserving_attempt", "error_type": type(exc).__name__,
                              "details": "Inspect private receipts; no automatic resubmission"}), flush=True)
            sys.exit(1)
