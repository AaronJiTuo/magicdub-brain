"""One real Bailian upload + existing MagicDub Fun-ASR path; no fal requests."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
import soundfile as sf


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def safe_error(body):
    return {k: re.sub(r"(?:https?|oss)://\S+", "[URL omitted]", str(body[k]))[:400]
            for k in ("code", "message", "request_id") if body.get(k)}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--run-id", help="Explicit new test run; omit to inspect/resume the original run")
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime.resolve() / "src"))
    from magicdub import config, pipeline
    from magicdub.common import DubError, read
    from magicdub.models import selection
    from magicdub.transport import Run

    root = Path(__file__).resolve().parent
    if args.run_id:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
            raise ValueError("Invalid run id")
        output = root / "runs" / args.run_id
    else:
        output = root
    output.mkdir(parents=True, exist_ok=True)
    private = root / "private" / args.run_id if args.run_id else root / "private"
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)
    summary_path = output / "summary.json"
    summary = read(summary_path) if summary_path.exists() else {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "started", "source_project": args.source.parent.parent.name,
        "model": "fun-asr", "parameters": {"diarization_enabled": True, "language_hints": ["en"]},
        "fal_calls": 0, "asr_submission_limit": 1,
    }
    if summary["status"] == "passed":
        print("Already passed; no new network requests.")
        return
    stage = "prepare"
    started = time.monotonic()
    try:
        info = sf.info(args.source)
        if (info.samplerate, info.channels, info.subtype) != (16000, 1, "PCM_16") or info.duration > 60:
            raise ValueError("Input must be <=60 seconds, 16k mono PCM16")
        subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(args.source),
                        "-f", "null", "-"], check=True, capture_output=True)
        sha = hashlib.sha256(args.source.read_bytes()).hexdigest()
        if summary.get("input_sha256") not in (None, sha):
            raise ValueError("Input changed; do not reuse this run")
        summary.update(input_sha256=sha, duration_seconds=info.duration,
                       bytes=args.source.stat().st_size, input_decode="passed")
        base = config.load().get("dashscope_base", "https://dashscope.aliyuncs.com/api/v1")
        parsed_base = urlparse(base)
        if not (parsed_base.scheme == "https" and parsed_base.path == "/api/v1" and
                (parsed_base.hostname == "dashscope.aliyuncs.com" or
                 (parsed_base.hostname or "").endswith(".cn-beijing.maas.aliyuncs.com"))):
            raise ValueError("This bounded test requires a configured official Beijing base")
        if summary.get("base") not in (None, base):
            raise ValueError("Base changed; start an explicit new run")
        config.credentials()
        key = os.environ.get("DASHSCOPE_API_KEY")
        if not key:
            raise ValueError("Missing configured DASHSCOPE_API_KEY")
        summary["base"] = base
        summary["runtime_fun_asr_sha256"] = hashlib.sha256(
            (args.runtime / "src/magicdub/fun_asr.py").read_bytes()).hexdigest()
        auth = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
        receipt = private / "upload-receipt.json"
        if receipt.exists():
            uploaded = read(receipt)
            if uploaded["input_sha256"] != sha:
                raise ValueError("Upload receipt input mismatch")
            oss_url = uploaded["oss_url"]
        else:
            if (private / "upload-sending.json").exists():
                raise ValueError("Upload result unknown; no automatic re-upload")
            stage = "upload_policy"
            response = requests.get(base + "/uploads", headers=auth,
                                    params={"action": "getPolicy", "model": "fun-asr"}, timeout=(15, 60))
            summary["upload_policy_http"] = response.status_code
            body = response.json()
            if response.status_code != 200 or "data" not in body:
                summary["error"] = safe_error(body)
                raise ValueError("Upload policy rejected")
            data = body["data"]
            host = urlparse(data["upload_host"])
            if host.scheme != "https" or not (host.hostname or "").endswith(".aliyuncs.com"):
                raise ValueError("Unexpected upload host")
            object_key = data["upload_dir"] + "/two-speakers-32s.wav"
            fields = {
                "OSSAccessKeyId": (None, data["oss_access_key_id"]),
                "Signature": (None, data["signature"]), "policy": (None, data["policy"]),
                "x-oss-object-acl": (None, data["x_oss_object_acl"]),
                "x-oss-forbid-overwrite": (None, data["x_oss_forbid_overwrite"]),
                "key": (None, object_key), "success_action_status": (None, "200"),
            }
            stage = "upload_file"
            save(private / "upload-sending.json", {"input_sha256": sha})
            t = time.monotonic()
            with args.source.open("rb") as stream:
                fields["file"] = ("two-speakers-32s.wav", stream, "audio/wav")
                response = requests.post(data["upload_host"], files=fields, timeout=(15, 90))
            summary.update(upload_http=response.status_code, upload_seconds=round(time.monotonic() - t, 3),
                           upload_host=host.hostname)
            save(summary_path, summary)
            if response.status_code != 200:
                raise ValueError("File upload rejected")
            oss_url = "oss://" + object_key
            save(receipt, {"oss_url": oss_url, "input_sha256": sha})
            print("Bailian upload HTTP 200", flush=True)

        project = private / "project"
        (project / "separation").mkdir(parents=True, exist_ok=True)
        if not (project / "project.json").exists():
            shutil.copyfile(args.source, project / "separation/vocals.wav")
            save(project / "project.json", {
                "schema_version": 1, "project_id": "bailian-upload-funasr-validation",
                "active_task": "single-real-validation", "source_language": "en",
                "duration_ms": round(info.duration * 1000), "stages": {},
                "models": selection("fun-asr", "demucs"), "fun_asr_media_url": oss_url,
            })

        class SingleAttemptRun(Run):
            def upload(self, name):
                raise AssertionError("fal upload must not run in this test")

            def _attempt(self, *a, **kw):
                attempts = list((self.root / "attempts").glob("*/*/attempt.json"))
                if any(read(p).get("status") in ("failed", "FAILED", "CANCELLED") for p in attempts):
                    raise DubError("Single test task failed; no automatic paid retry")
                return super()._attempt(*a, **kw)

            def _save(self, folder, attempt):
                super()._save(folder, attempt)
                status = attempt.get("status")
                if status != getattr(self, "last_status", None):
                    print("Fun-ASR status:", status, flush=True)
                    self.last_status = status

        stage = "fun_asr"
        run = SingleAttemptRun(project)
        t = time.monotonic()
        pipeline.transcribe(run)
        summary["recognition_seconds"] = round(time.monotonic() - t, 3)
        transcript = read(project / "transcript.json")
        segments = transcript["segments"]
        summary.update(segment_count=len(segments), speakers=sorted({s["speaker"] for s in segments if s["speaker"] is not None}),
                       text_characters=len(transcript["text"]),
                       timestamps_valid=all(0 <= s["start_ms"] < s["end_ms"] <= round(info.duration*1000) for s in segments),
                       all_speakers_present=all(s["speaker"] is not None for s in segments))
        save(output / "transcript.json", transcript)
        if not (segments and summary["timestamps_valid"] and summary["all_speakers_present"]):
            raise ValueError("Result validation failed")
        summary["status"] = "passed"
    except Exception as exc:
        summary.update(status="stopped", stopped_stage=stage, exception_type=type(exc).__name__)
    finally:
        project = private / "project"
        attempts = list((project / "attempts").glob("*/*/attempt.json"))
        summary["asr_attempt_count"] = len(attempts)
        if attempts:
            a = read(attempts[-1])
            summary["asr_attempt"] = {k: a[k] for k in ("status", "request_id", "submit_http_status", "usage", "cost_status", "estimated_amount", "currency", "pricing") if k in a}
            f = attempts[-1].parent
            if (f / "submission.json").exists():
                summary["submission"] = safe_error(read(f / "submission.json"))
            if (f / "status.json").exists():
                status = read(f / "status.json")
                summary["provider_task_status"] = status.get("output", {}).get("task_status")
                summary["provider_file_statuses"] = [{k: s[k] for k in ("subtask_status", "code", "message") if k in s}
                                                    for s in status.get("output", {}).get("results", [])]
                summary["usage"] = status.get("usage")
        summary["elapsed_seconds_this_run"] = round(time.monotonic() - started, 3)
        summary["updated_at"] = datetime.now(timezone.utc).isoformat()
        save(summary_path, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if summary["status"] != "passed":
        sys.exit(2)


if __name__ == "__main__":
    main()
