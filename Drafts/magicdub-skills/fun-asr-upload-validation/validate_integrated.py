"""One real task through production preprocessing, stage upload, ASR and parsing."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime.resolve() / "src"))
    import fal_client
    import requests
    import soundfile as sf
    from magicdub import audio_quality, config, fun_asr, pipeline
    from magicdub.common import DubError, digest, now, read, write
    from magicdub.models import selection
    from magicdub.transport import Run

    root = Path(__file__).resolve().parent
    output = root / "runs/integrated-routing"
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "summary.json"
    if summary_path.exists() and read(summary_path).get("status") == "passed":
        print("Already passed; no new requests.")
        return
    project = root / "private/integrated-routing/project"
    config.credentials()
    base = config.dashscope_base()
    if not config.beijing_base(base):
        raise ValueError("This validation requires the configured Beijing base")
    source_info = sf.info(args.source)
    if not 0 < source_info.duration <= 60:
        raise ValueError("This validation requires a sample of at most 60 seconds")
    source_sha = digest(args.source)
    if not (project / "project.json").exists():
        (project / "separation").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.source, project / "separation/vocals.wav")
        write(project / "project.json", {
            "schema_version": 1, "project_id": "integrated-funasr-validation",
            "active_task": "single-real-task", "source_language": "en", "target_language": "zh-Hans",
            "duration_ms": round(source_info.duration * 1000), "stages": {},
            "models": selection("fun-asr", "demucs"), "audio_policy": {"version": 1},
            "validation_source_sha256": source_sha, "validation_base": base,
        })
    existing = read(project / "project.json")
    if existing["validation_source_sha256"] != source_sha or existing["validation_base"] != base:
        raise ValueError("Source/base changed; do not reuse this test project")

    class SingleTaskRun(Run):
        def _attempt(self, *a, **kw):
            saved = list(self.root.glob("attempts/*/*/attempt.json"))
            if any(read(p).get("status") in ("failed", "FAILED", "CANCELLED") for p in saved):
                raise DubError("Single validation task failed; no automatic paid retry")
            return super()._attempt(*a, **kw)

    run = SingleTaskRun(project)
    summary = {"started_at": now(), "status": "started", "input_sha256": source_sha,
               "duration_seconds": source_info.duration, "runtime": "local-unpublished-source",
               "source_fun_asr_sha256": digest(args.runtime / "src/magicdub/fun_asr.py"),
               "base_type": "workspace-beijing" if ".maas." in base else "public-beijing",
               "parameters": {**run.project["models"]["asr"]["parameters"], "language_hints": ["en"]},
               "network": {"upload_policy": 0, "file_upload": 0, "asr_submit": 0, "fal": 0}}
    real_get, real_post = requests.get, requests.post

    def get(url, **kwargs):
        response = real_get(url, **kwargs)
        if url == base + "/uploads":
            summary["network"]["upload_policy"] += 1
            summary["upload_policy_http"] = response.status_code
        return response

    def post(url, **kwargs):
        stage = "asr_submit" if url == base + "/services/audio/asr/transcription" else "file_upload"
        if summary["network"][stage] >= 1:
            raise DubError("At most one upload and one ASR submission per invocation")
        summary["network"][stage] += 1
        if stage == "asr_submit":
            assert kwargs["json"]["input"]["file_urls"][0].startswith("oss://")
            assert kwargs["headers"]["X-DashScope-OssResourceResolve"] == "enable"
        else:
            assert (urlparse(url).hostname or "").endswith(".aliyuncs.com")
        response = real_post(url, **kwargs)
        summary[stage + "_http"] = response.status_code
        return response

    def no_fal(*a, **kw):
        summary["network"]["fal"] += 1
        raise DubError("Fal must not be used in this validation")

    requests.get, requests.post = get, post
    fal_client.upload_file = no_fal
    start = time.monotonic()
    try:
        asr_file = run.path(audio_quality.asr_audio(run, required=True))
        info = sf.info(asr_file)
        assert (info.samplerate, info.channels, info.subtype) == (16000, 1, "PCM_16")
        assert abs(info.duration - source_info.duration) <= 1 / 16000
        subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(asr_file), "-f", "null", "-"],
                       check=True, capture_output=True)
        summary["processed_audio"] = {"sha256": digest(asr_file), "sample_rate": info.samplerate,
                                      "channels": info.channels, "subtype": info.subtype, "decode": "passed"}
        pipeline.transcribe(run)
        transcript = read(project / "transcript.json")
        segments = transcript["segments"]
        summary["segment_count"] = len(segments)
        summary["speakers"] = run.project["speakers"]
        summary["timestamps_valid"] = all(0 <= s["start_ms"] < s["end_ms"] <= run.project["duration_ms"]
                                            for s in segments)
        assert segments and summary["timestamps_valid"] and all(s["speaker"] is not None for s in segments)
        write(output / "transcript.json", transcript)
        counts = dict(summary["network"])
        fun_asr.transcribe(run)
        summary["cached_result_without_network"] = summary["network"] == counts
        assert summary["cached_result_without_network"]
        assert digest(args.source) == source_sha
        summary["source_unchanged"] = True
        summary["status"] = "passed"
    except Exception as exc:
        summary.update(status="stopped", exception_type=type(exc).__name__)
    finally:
        attempts = list(project.glob("attempts/*/*/attempt.json"))
        summary["asr_attempt_count"] = len(attempts)
        if attempts:
            a = read(attempts[-1])
            summary["attempt"] = {k: a[k] for k in ("status", "request_id", "usage", "submit_http_status",
                                                    "cost_status", "estimated_amount", "currency") if k in a}
        summary["elapsed_seconds"] = round(time.monotonic() - start, 3)
        summary["finished_at"] = now()
        write(summary_path, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if summary["status"] != "passed":
        sys.exit(2)


if __name__ == "__main__":
    main()
