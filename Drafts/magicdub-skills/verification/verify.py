"""Standalone media experiment. No imports or dependency on the old MagicDub engine."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import fal_client
import numpy as np
import requests
import soundfile as sf
from dotenv import load_dotenv
from costs import set_cost, summarize

SR = 48000
ENDPOINTS = {"demucs": "fal-ai/demucs", "sam": "fal-ai/sam-audio/separate",
             "asr": "fal-ai/whisper", "tts": "fal-ai/index-tts-2/text-to-speech"}


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def log(event, **fields):
    print(json.dumps({"time": now(), "event": event, **fields}, ensure_ascii=False), flush=True)


def ff(*args):
    # All paths/parameters are separate argv values, never interpolated into a shell.
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *map(str, args)], check=True)


def probe(path):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]))


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class Run:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.project = read(self.root / "project.json")
        self.headers = {"Authorization": "Key " + os.environ.get("FAL_KEY", ""),
                        "X-Fal-No-Retry": "1", "x-app-fal-disable-fallback": "true"}

    def path(self, name):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save(self):
        write(self.path("project.json"), self.project)

    def get(self, url, **kwargs):
        for n in range(4):
            try:
                response = requests.get(url, timeout=(15, 90), **kwargs)
                if response.status_code not in (429, 500, 502, 503, 504):
                    return response
            except requests.RequestException:
                if n == 3:
                    raise RuntimeError("GET transport failure; saved request can be resumed") from None
            time.sleep(2 ** n)
        return response

    def upload(self, name):
        path = self.path(name)
        cache_path = self.path("remote/uploads.json")
        cache = read(cache_path) if cache_path.exists() else {}
        key = digest(path)
        if key not in cache:
            log("upload", artifact=name)
            cache[key] = {"url": fal_client.upload_file(str(path)), "created_at": now(), "artifact": name}
            write(cache_path, cache)
        return cache[key]["url"]

    def call(self, stage, endpoint, payload):
        # Payload hashes include URLs: once submitted the input and remote task are immutable.
        folder = self.path(f"attempts/{stage}")
        folder.mkdir(exist_ok=True)
        attempt_path = folder / "attempt.json"
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if attempt_path.exists():
            attempt = read(attempt_path)
            if attempt["input_sha256"] != fingerprint or attempt["endpoint"] != endpoint:
                raise RuntimeError("Existing attempt input changed; use a new explicit stage revision")
            if (folder / "result.json").exists():
                log("reuse_result", stage=stage, request_id=attempt.get("request_id"))
                return read(folder / "result.json")
            if not attempt.get("request_id"):
                raise RuntimeError("Submission outcome unknown or rejected; inspect saved attempt before retry")
        else:
            attempt = {"stage": stage, "endpoint": endpoint, "input_sha256": fingerprint,
                       "started_at": now(), "status": "submitting",
                       "ledger_id": f"{self.root.name}/{stage}", "submission_attempts": 1}
            set_cost(attempt, "USD")
            write(folder / "input.json", payload)
            write(attempt_path, attempt)
            try:
                response = requests.post("https://queue.fal.run/" + endpoint, json=payload,
                                         headers=self.headers, timeout=(15, 90))
            except requests.RequestException:
                attempt["status"] = "submission_unknown"
                write(attempt_path, attempt)
                raise RuntimeError("POST outcome unknown; no automatic resubmission") from None
            attempt["submit_http_status"] = response.status_code
            try:
                submitted = response.json()
            except ValueError:
                submitted = {}
            write(folder / "submission.json", submitted)
            if response.status_code >= 400 or not submitted.get("request_id"):
                attempt["status"] = "submission_rejected" if response.status_code < 500 else "submission_unknown"
                write(attempt_path, attempt)
                raise RuntimeError(f"Submission HTTP {response.status_code}; evidence saved locally")
            attempt.update({k: submitted[k] for k in ("request_id", "status_url", "response_url")})
            attempt["status"] = "submitted"
            write(attempt_path, attempt)
            log("submitted", stage=stage, request_id=attempt["request_id"])
        deadline = time.monotonic() + 1800
        last = None
        while time.monotonic() < deadline:
            response = self.get(attempt["status_url"], headers=self.headers)
            if response.status_code >= 400:
                raise RuntimeError(f"Status HTTP {response.status_code}; request retained")
            status = response.json()
            write(folder / "status.json", status)
            if status.get("status") != last:
                last = status.get("status")
                log("queue", stage=stage, status=last)
            attempt["status"] = last
            write(attempt_path, attempt)
            if last == "COMPLETED":
                response = self.get(attempt["response_url"], headers=self.headers)
                result = response.json()
                attempt["billable_units_header"] = response.headers.get("x-fal-billable-units")
                if response.status_code >= 400:
                    write(folder / "error.json", result)
                    attempt.update(status="failed", finished_at=now(), result_http_status=response.status_code)
                    write(attempt_path, attempt)
                    raise RuntimeError(f"Model failure HTTP {response.status_code}; cost remains pending")
                if isinstance(result, dict) and "data" in result:
                    result = result["data"]
                write(folder / "result.json", result)
                attempt.update(status="succeeded", finished_at=now(),
                               billable_units_header=response.headers.get("x-fal-billable-units"))
                write(attempt_path, attempt)
                return result
            if last in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Remote task {last}; evidence retained")
            time.sleep(5)
        raise RuntimeError("Local wait deadline reached; resume existing remote task")

    def download(self, obj, name):
        path = self.path(name)
        if path.exists():
            return path
        url = obj["url"] if isinstance(obj, dict) else obj
        response = self.get(url)
        if response.status_code != 200:
            raise RuntimeError(f"Media download HTTP {response.status_code}")
        temp = path.with_suffix(path.suffix + ".download")
        temp.write_bytes(response.content)
        probe(temp)
        temp.replace(path)
        return path


def init(args):
    root = Path(args.run).resolve()
    if (root / "project.json").exists():
        raise RuntimeError("Project already exists; use a new run or resume a stage")
    source = Path(args.source).resolve()
    info = probe(source)
    (root / "source").mkdir(parents=True, exist_ok=True)
    copied = root / "source" / source.name
    shutil.copy2(source, copied)
    ff("-ss", args.start, "-i", copied, "-t", args.duration, "-map", "0:v:0", "-map", "0:a:0",
       "-c:v", "libx264", "-crf", 18, "-preset", "fast", "-c:a", "aac", "-movflags", "+faststart", root / "source/clip.mp4")
    ff("-i", root / "source/clip.mp4", "-vn", "-ar", SR, "-ac", 2, "-c:a", "pcm_s16le", root / "source/audio.wav")
    write(root / "source/probe.json", info)
    write(root / "project.json", {"schema_version": 1, "created_at": now(), "source": str(copied.relative_to(root)),
          "source_sha256": digest(copied), "source_duration_seconds": float(info["format"]["duration"]),
          "clip_start_ms": round(args.start * 1000), "duration_ms": round(args.duration * 1000),
          "source_language": "en", "target_language": "zh-Hans", "status": "prepared",
          "models": {"asr": ENDPOINTS["asr"], "tts": ENDPOINTS["tts"], "translation": "current_agent"},
          "translation_cost": "host agent cost unmeasured and excluded"})
    log("prepared", duration_seconds=args.duration, source_sha256=digest(copied))


def separate(run, model, stage="separation", source_audio="source/audio.wav"):
    endpoint = ENDPOINTS[model]
    run.project["models"]["separation"] = endpoint
    run.save()
    payload = {"audio_url": run.upload(source_audio), "output_format": "wav"}
    if model == "demucs":
        payload.update(model="htdemucs_ft", stems=["vocals"], shifts=1, overlap=0.25)
    else:
        payload.update(prompt="speech", predict_spans=False, acceleration="balanced", output_format="mp3",
                       reranking_candidates=1, max_chunk_duration=60, chunk_overlap=5)
    result = run.call(stage, endpoint, payload)
    prefix = f"separation/{stage}"
    suffix = "wav" if model == "demucs" else "mp3"
    raw = run.download(result["vocals"] if model == "demucs" else result["target"], f"{prefix}/vocals_raw.{suffix}")
    vocals = run.path(f"{prefix}/vocals.wav")
    background = run.path(f"{prefix}/background.wav")
    source_info = probe(run.path(source_audio))["streams"][0]
    sample_rate, channels = int(source_info["sample_rate"]), int(source_info["channels"])
    ff("-i", raw, "-ar", sample_rate, "-ac", channels, "-c:a", "pcm_s24le", vocals)
    # Use the subtraction gain from the old project's implementation, preserving all
    # original material except 0.98 times the extracted voice. Never import its engine.
    length = run.project["duration_ms"] / 1000
    layout = "mono" if channels == 1 else "stereo"
    ff("-i", run.path(source_audio), "-i", vocals,
       "-filter_complex", f"[0:a]aformat=sample_fmts=fltp:channel_layouts={layout}[m];[1:a]aformat=sample_fmts=fltp:channel_layouts={layout},volume=-0.98[v];[m][v]amix=inputs=2:normalize=0,alimiter=limit=0.95:level=0:latency=1,apad,atrim=duration={length}[a]",
       "-map", "[a]", "-ar", sample_rate, "-c:a", "pcm_s24le", background)
    if model == "sam":
        run.download(result["residual"], f"{prefix}/provider_residual.mp3")
    run.project.update(separation_vocals_artifact=str(vocals.relative_to(run.root)),
                       separation_background_artifact=str(background.relative_to(run.root)),
                       separation_attempt=stage, background_subtract_gain=0.98,
                       separation_input_artifact=source_audio, reference_sample_rate=sample_rate)
    run.project["status"] = "separated"
    run.save()
    log("separated", model=endpoint)


def asr(run, artifact="separation/vocals.wav"):
    run.project["asr_input"] = artifact
    run.save()
    result = run.call("asr", ENDPOINTS["asr"], {"audio_url": run.upload(artifact),
                      "task": "transcribe", "language": "en", "chunk_level": "segment", "diarize": True})
    segments = []
    for n, chunk in enumerate(result["chunks"]):
        start, end = chunk["timestamp"]
        if start is None or end is None:
            raise RuntimeError("ASR missing timestamps; preserve result for repair")
        segments.append({"id": f"seg_{n+1:04d}", "start_ms": round(start * 1000),
                         "end_ms": min(round(end * 1000), run.project["duration_ms"]),
                         "speaker": chunk.get("speaker") or "speaker_0", "source_text": chunk["text"].strip(),
                         "translated_text": None, "flags": []})
    write(run.path("asr/chunks.json"), {"schema_version": 1, "segments": segments})
    utterances = []
    for s in segments:
        if (utterances and utterances[-1]["speaker"] == s["speaker"]
                and not re.search(r'[.!?][\"\x27]?$' , utterances[-1]["source_text"])
                and s["start_ms"] - utterances[-1]["end_ms"] <= 700):
            utterances[-1]["source_text"] += " " + s["source_text"]
            utterances[-1]["end_ms"] = s["end_ms"]
            utterances[-1]["source_segment_ids"].append(s["id"])
        else:
            utterances.append({**s, "id": f"utt_{len(utterances)+1:04d}", "source_segment_ids": [s["id"]]})
    write(run.path("transcript.json"), {"schema_version": 1, "segments": utterances})
    run.project["status"] = "awaiting_agent_translation"
    run.save()
    log("transcribed", chunks=len(segments), utterances=len(utterances), speakers=sorted({s["speaker"] for s in segments}))


def atempo(ratio):
    factors = []
    while ratio > 2:
        factors.append(2)
        ratio /= 2
    while ratio < .5:
        factors.append(.5)
        ratio /= .5
    factors.append(ratio)
    return ",".join(f"atempo={v:.12g}" for v in factors)


def tts(run, revision="legacy_v2"):
    data = read(run.path("translations.json"))
    segments = data["segments"]
    original = {s["id"]: s for s in read(run.path("transcript.json"))["segments"]}
    if {s["id"] for s in segments} != set(original):
        raise RuntimeError("Translation segment IDs must cover transcript exactly")
    for s in segments:
        if not s["translated_text"] or s["end_ms"] <= s["start_ms"]:
            raise RuntimeError("Missing translation or invalid time window")
    run.project["active_alignment"] = f"alignment_{revision}.json"
    run.project["tts_reference_strategy"] = "each original utterance as timbre and emotional reference"
    run.save()
    aligned = []
    for s in segments:
        reference = f"voices/{revision}/{s['id']}.wav"
        if not run.path(reference).exists():
            ff("-ss", s["start_ms"] / 1000, "-i", run.path(run.project["separation_vocals_artifact"]),
               "-t", (s["end_ms"] - s["start_ms"]) / 1000, "-ar", run.project.get("reference_sample_rate", SR), "-ac", 1, run.path(reference))
        url = run.upload(reference)
        stage = f"tts_{revision}_{s['id']}"
        result = run.call(stage, ENDPOINTS["tts"],
                          {"audio_url": url, "prompt": s["translated_text"], "emotional_audio_url": url})
        raw = run.download(result["audio"], f"tts/{revision}/{s['id']}.wav")
        attempt_path = run.path(f"attempts/{stage}/attempt.json")
        attempt = read(attempt_path)
        attempt["output_artifact"] = str(raw.relative_to(run.root))
        write(attempt_path, attempt)
        duration = float(probe(raw)["format"]["duration"])
        target = (s["end_ms"] - s["start_ms"]) / 1000
        ratio = duration / target
        if ratio <= 0:
            raise RuntimeError("Empty speech output")
        samples = round(target * SR)
        path = run.path(f"aligned/{revision}/{s['id']}.wav")
        ff("-i", raw, "-af", atempo(ratio) + f",aresample={SR},apad=whole_len={samples},atrim=end_sample={samples}",
           "-ar", SR, "-ac", 1, "-c:a", "pcm_s24le", path)
        if abs(sf.info(path).frames - samples) > 1:
            raise RuntimeError("Alignment sample count mismatch")
        flags = s.get("flags", []) + (["strong_time_stretch"] if ratio < .75 or ratio > 1.35 else [])
        aligned.append({**s, "tts_duration_seconds": duration, "tempo_ratio": ratio,
                        "aligned_artifact": str(path.relative_to(run.root)), "flags": flags})
        write(run.path(run.project["active_alignment"]), {"sample_rate": SR, "segments": aligned})
        log("aligned", segment=s["id"], tempo_ratio=round(ratio, 3), flags=flags)
    run.project["status"] = "voiced"
    run.save()


def export(run):
    segments = read(run.path(run.project.get("active_alignment", "alignment.json")))["segments"]
    revision = Path(run.project.get("active_alignment", "alignment.json")).stem
    mix_prefix = f"mix/{revision}"
    if len(segments) != len(read(run.path("translations.json"))["segments"]):
        raise RuntimeError("Cannot export a technically incomplete set of speech segments")
    length = round(run.project["duration_ms"] * SR / 1000)
    timeline = np.zeros(length, dtype=np.float64)
    for s in segments:
        audio, rate = sf.read(run.path(s["aligned_artifact"]))
        if rate != SR:
            raise RuntimeError("Unexpected sample rate")
        start = round(s["start_ms"] * SR / 1000)
        stop = min(length, start + len(audio))
        timeline[start:stop] += audio[:stop-start]
    # Preserve each utterance's relative loudness and apply a single safe global gain.
    peak = float(np.max(np.abs(timeline)))
    gain = min(2, .88 / peak) if peak else 1
    sf.write(run.path(f"{mix_prefix}/speech.wav"), timeline * gain, SR, subtype="PCM_24")
    ff("-i", run.path(f"{mix_prefix}/speech.wav"), "-i", run.path(run.project["separation_background_artifact"]),
       "-filter_complex", f"[0:a]pan=stereo|c0=c0|c1=c0[v];[v][1:a]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95:level=0:latency=1,apad,atrim=end_sample={length}[a]",
       "-map", "[a]", "-ar", SR, "-c:a", "pcm_s24le", run.path(f"{mix_prefix}/final.wav"))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video = run.path(f"exports/stevejobs_zh-Hans_{stamp}.mp4")
    ff("-i", run.path("source/clip.mp4"), "-i", run.path(f"{mix_prefix}/final.wav"), "-map", "0:v:0", "-map", "1:a:0",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", run.project["duration_ms"] / 1000,
       "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", video)
    ff("-v", "error", "-i", video, "-f", "null", "-")
    checks = {"full_decode": "passed", "export": str(video.relative_to(run.root)), "probe": probe(video),
              "expected_segments": len(segments), "aligned_segments": len(segments), "speech_gain": gain,
              "flagged_segments": [s["id"] for s in segments if s["flags"]], "subjective_listening": "not_verified"}
    write(run.path("checks.json"), checks)
    run.project.update(status="exported_with_quality_flags" if checks["flagged_segments"] else "exported",
                       latest_export=str(video.relative_to(run.root)), latest_mix=f"{mix_prefix}/final.wav")
    run.save()
    log("exported", artifact=str(video.relative_to(run.root)), duration_seconds=checks["probe"]["format"]["duration"],
        flagged_segments=len(checks["flagged_segments"]))


def billing(run):
    files = sorted(run.root.glob("attempts/*/attempt.json"))
    attempts = [read(p) for p in files]
    # Calculate from the provider's source amounts each time, never multiply
    # already-converted CNY again when a run is resumed or reconciled.
    for a in attempts:
        source = a.get("source_cost")
        if source is not None:
            a.update(currency=source["currency"], amount=source.get("amount"),
                     estimated_amount=source.get("estimated_amount"))
    prices = run.get("https://api.fal.ai/v1/models/pricing", headers=run.headers,
                     params={"endpoint_id": ",".join(sorted({a["endpoint"] for a in attempts}))}) if attempts else None
    if prices is not None:
        write(run.path("cost/pricing.json"), {"checked_at": now(), "http_status": prices.status_code, "data": prices.json()})
    price_map = {p["endpoint_id"]: p for p in prices.json().get("prices", [])} if prices is not None and prices.ok else {}
    events = []
    billing_status = None
    billing_headers = {**run.headers, "Authorization": "Key " + os.environ.get("FAL_BILLING_KEY", os.environ.get("FAL_KEY", ""))}
    ids = [a["request_id"] for a in attempts if a.get("request_id")]
    for i in range(0, len(ids), 50):
        params = {"request_id": ",".join(ids[i:i+50]), "limit": 100}
        while True:
            response = run.get("https://api.fal.ai/v1/models/billing-events", headers=billing_headers, params=params)
            billing_status = response.status_code
            if response.status_code != 200:
                break
            page = response.json()
            events.extend(page["billing_events"])
            if not page.get("has_more"):
                break
            params["cursor"] = page["next_cursor"]
    write(run.path("cost/billing-events.json"), {"checked_at": now(), "http_status": billing_status, "billing_events": events})
    for path, a in zip(files, attempts):
        matched = [e for e in events if e["request_id"] == a.get("request_id")]
        if matched:
            a.update(cost_status="confirmed", amount=str(sum((Decimal(str(e["cost_total"])) for e in matched), Decimal(0))))
            a.pop("estimated_amount", None)
        elif a.get("cost_status") != "confirmed" and a.get("endpoint") in price_map:
            price = price_map[a["endpoint"]]
            units, basis = a.get("billable_units_header"), "response billable units times current price; not reconciled"
            if not units and price["unit"] == "compute seconds":
                status_file = path.parent / "status.json"
                status = read(status_file) if status_file.exists() else {}
                units = status.get("metrics", {}).get("inference_time")
                basis = "runner inference time times current compute-second price; billing not reconciled"
            if not units and a["stage"].startswith("tts_"):
                audio = run.root / a["output_artifact"] if a.get("output_artifact") else run.root / "tts" / (a["stage"][4:] + ".wav")
                if audio.exists() and price["unit"] == "seconds":
                    units = probe(audio)["format"]["duration"]
                    basis = "generated audio duration times current price; rounding and billing not reconciled"
            if not units and a["stage"].startswith("separation") and a["status"] == "succeeded" and price["unit"] == "seconds":
                units = Decimal(run.project["duration_ms"]) / 1000
                basis = "input audio duration times current per-second price; billing not reconciled"
            if not units and a["endpoint"] == ENDPOINTS["sam"] and a["status"] == "succeeded" and price["unit"] == "units":
                units = Decimal(run.project["duration_ms"]) / 30000
                basis = "nominal 90-second clip / 30-second unit; one candidate; provider rounding and billing not reconciled; https://fal.ai/models/fal-ai/sam-audio/separate"
            if units is not None and price.get("currency") in ("USD", "CNY"):
                try:
                    estimated = Decimal(str(units)) * Decimal(str(price["unit_price"]))
                    a.update(currency=price["currency"], cost_status="estimated", estimated_amount=str(estimated), estimate_basis=basis)
                except Exception:
                    pass
        a["ledger_id"] = f"{run.root.name}/{a['stage']}"
        set_cost(a, a.get("currency", "USD"),
                 amount=a.get("amount") if a["cost_status"] == "confirmed" else None,
                 estimated_amount=a.get("estimated_amount") if a["cost_status"] == "estimated" else None,
                 basis=a.get("estimate_basis"))
        write(path, a)
    summary = {**summarize(attempts), "checked_at": now(), "billing_http_status": billing_status}
    write(run.path("cost/summary.json"), summary)
    log("cost", display=summary["display"], pending=len(summary["pending_attempts"]), billing_http_status=billing_status)


def qc(run, stage="qc_asr"):
    result = run.call(stage, ENDPOINTS["asr"], {"audio_url": run.upload(run.project.get("latest_mix", "mix/final.wav")),
                      "task": "transcribe", "chunk_level": "segment", "diarize": False})
    write(run.path("qc/roundtrip_asr.json"), result)
    segments = read(run.path(run.project["active_alignment"]))["segments"]
    checks = []
    for s in segments:
        audio, sr = sf.read(run.path(s["aligned_artifact"]))
        target = round((s["end_ms"] - s["start_ms"]) * SR / 1000)
        checks.append({"id": s["id"], "expected_samples": target, "actual_samples": len(audio),
                       "sample_rate": sr, "rms": float(np.sqrt(np.mean(audio * audio))),
                       "peak": float(np.max(np.abs(audio))), "tempo_ratio": s["tempo_ratio"]})
    write(run.path("qc/audio_checks.json"), {"segments": checks, "all_non_silent": all(s["rms"] > 1e-5 for s in checks),
          "all_durations_match": all(s["expected_samples"] == s["actual_samples"] and s["sample_rate"] == SR for s in checks)})
    log("qc_complete", segments=len(checks), roundtrip_text=result.get("text", ""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "separate", "asr", "tts", "export", "billing", "qc"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--credentials")
    parser.add_argument("--source")
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--separation", choices=["demucs", "sam"])
    parser.add_argument("--stage", default="separation", help="Separate explicit attempts without overwriting earlier request evidence")
    parser.add_argument("--separation-input", default="source/audio.wav")
    parser.add_argument("--tts-revision", default="legacy_v2")
    parser.add_argument("--qc-stage", default="qc_asr")
    parser.add_argument("--asr-input", choices=["source/audio.wav", "separation/vocals.wav"], default="separation/vocals.wav")
    args = parser.parse_args()
    if args.credentials:
        load_dotenv(args.credentials, override=False)
    try:
        if args.command == "init":
            init(args)
            return
        run = Run(args.run)
        if args.command in ("separate", "asr", "tts", "billing", "qc") and not os.environ.get("FAL_KEY"):
            raise RuntimeError("FAL_KEY not configured")
        if args.command == "separate":
            if not args.separation:
                raise RuntimeError("Explicit separation choice required")
            separate(run, args.separation, args.stage, args.separation_input)
        elif args.command == "asr":
            asr(run, args.asr_input)
        elif args.command == "tts":
            tts(run, args.tts_revision)
        elif args.command == "qc":
            qc(run, args.qc_stage)
        else:
            globals()[args.command](run)
    except KeyboardInterrupt:
        log("interrupted", message="Stopped locally; remote task IDs and costs are retained")
        raise SystemExit(130) from None
    except Exception as exc:
        # Deliberately omit repr/traceback: HTTP exceptions can contain signed URLs.
        log("error", type=type(exc).__name__, message=str(exc) if isinstance(exc, RuntimeError) else "Inspect local artifacts; no credentials logged")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
