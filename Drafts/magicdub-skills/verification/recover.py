"""Use Whisper diarization with the recovered test_by_step media parameters.

Only imports this experiment's transport helpers, never the legacy engine.
Use a new run directory; baseline outputs and legacy experiments stay intact.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from dotenv import load_dotenv

from verify import Run, billing, digest, ff, log, now, probe, read, write

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parents[1] / "test_by_step"


def prepare(root, baseline, separation):
    if (root / "project.json").exists():
        raise RuntimeError("Run exists; resume a stage instead")
    original = read(baseline / "project.json")
    root.mkdir(parents=True, exist_ok=True)
    (root / "source").mkdir()
    for name in [original["source"], "source/clip.mp4"]:
        shutil.copy2(baseline / name, root / name)
    # Extract from the original, avoiding the baseline clip's intermediate AAC encode.
    ff("-i", root / original["source"], "-ss", original["clip_start_ms"] / 1000,
       "-t", original["duration_ms"] / 1000, "-vn", "-acodec", "pcm_s16le",
       "-ar", "16000", "-ac", "1", root / "source/audio_16k_mono.wav")
    sources = {}
    for name in ["fetch_audio.py", "separate_audio.py", "asr.py", "build_sentences.py",
                 "translate_sentences.py", "cut_speech.py", "tts.py", "refine_target_audio.py",
                 "assemble_target_video.py", "source/prompt_system_gemini.txt"]:
        dest = root / "provenance/test_by_step" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LEGACY / name, dest)
        sources[name] = digest(dest)
    project = {k: original[k] for k in ["source", "source_sha256", "source_duration_seconds",
              "clip_start_ms", "duration_ms", "source_language", "target_language"]}
    project.update(schema_version=1, created_at=now(), status="prepared",
                   baseline_run=baseline.name, recovery_preset="test_by_step_media_with_whisper",
                   selected_separation=separation, historical_source_sha256=sources,
                   models={"asr": "fal-ai/whisper", "tts": "fal-ai/index-tts-2/text-to-speech",
                           "translation": "current_agent"},
                   cost_policy={"currency": "CNY", "usd_to_cny": "7", "display": "¥0.00"},
                   translation_cost="host agent cost unmeasured and excluded")
    project["asr_configuration"] = read(HERE / "whisper_parameters.json")
    write(root / "project.json", project)
    shutil.copy2(HERE / "recovered_parameters.json", root / "provenance/recovered_parameters.json")
    for name in ["recover.py", "verify.py", "costs.py", "whisper_parameters.json", "pyproject.toml", "uv.lock"]:
        shutil.copy2(HERE / name, root / "provenance" / name)
    log("recovery_prepared", run=root.name, separation=separation)


def separate(run):
    model = run.project["selected_separation"]
    payload = {"audio_url": run.upload("source/audio_16k_mono.wav")}
    if model == "demucs":
        endpoint = "fal-ai/demucs"
        payload.update(model="htdemucs_ft", stems=["vocals"], shifts=1, overlap=.25, output_format="wav")
    else:
        endpoint = "fal-ai/sam-audio/separate"
        payload.update(prompt="speech", predict_spans=False, reranking_candidates=1,
                       acceleration="balanced", max_chunk_duration=60, chunk_overlap=5, output_format="mp3")
    result = run.call("separation_recovered", endpoint, payload)
    raw = run.download(result["vocals" if model == "demucs" else "target"],
                       "separation/raw." + ("wav" if model == "demucs" else "mp3"))
    vocals = run.path("separation/vocals.wav")
    ff("-i", raw, "-ac", 1, "-ar", 16000, "-acodec", "pcm_s16le", vocals)
    source = run.path("source/audio_16k_mono.wav")
    d = max(.01, min(float(probe(source)["format"]["duration"]),
                      float(probe(vocals)["format"]["duration"])) - .02)
    trim = f"atrim=start=0:duration={d:.6f}"
    filt = (f"[0:a]{trim},aformat=sample_fmts=fltp:channel_layouts=mono[mx];"
            f"[1:a]{trim},aformat=sample_fmts=fltp:channel_layouts=mono,volume=0.98[vc];"
            "[mx][vc]amerge=inputs=2,pan=mono|c0=c0-c1,"
            "alimiter=level_in=1:level_out=0.95:limit=0.95,"
            "aformat=sample_fmts=s16:channel_layouts=mono[out]")
    ff("-i", source, "-i", vocals, "-filter_complex", filt, "-map", "[out]", run.path("separation/background.wav"))
    run.project.update(separation_vocals_artifact="separation/vocals.wav",
                       separation_background_artifact="separation/background.wav", status="separated")
    run.project["models"]["separation"] = endpoint
    run.save()


def transcribe(run):
    config = run.project.get("asr_configuration", {})
    required = {"task", "language", "chunk_level", "diarize", "batch_size", "prompt", "num_speakers"}
    if config.get("pending_decisions") or set(config.get("parameters", {})) != required:
        raise RuntimeError("Whisper parameter decisions are incomplete; no request submitted")
    if config["endpoint"] != "fal-ai/whisper" or config["parameters"]["diarize"] is not True:
        raise RuntimeError("Expected user-selected Whisper with diarization enabled")
    result = run.call("asr_whisper_diarized", config["endpoint"], {
        "audio_url": run.upload("separation/vocals.wav"), **config["parameters"]})
    write(run.path("asr/diarization_segments.json"), result.get("diarization_segments", []))
    segments = []
    for n, ch in enumerate(result["chunks"]):
        start, end = ch["timestamp"]
        if start is None or end is None or end <= start:
            raise RuntimeError("Invalid ASR timing; retained provider result")
        start_ms, end_ms = round(start * 1000), min(round(end * 1000), run.project["duration_ms"])
        if start_ms >= end_ms:
            raise RuntimeError("ASR outside clip")
        segments.append({"id": f"s{n:04d}", "start_ms": start_ms, "end_ms": end_ms,
                         "source_text": ch["text"].strip(), "translated_text": None,
                         "speaker": ch.get("speaker"),
                         "target_words": max(1, round((end_ms - start_ms) / 1000 * 4.5))})
    write(run.path("transcript.json"), {"schema_version": 1, "segments": segments,
                                      "text": result.get("text", ""), "post_merge": False})
    run.project["status"] = "awaiting_translation"
    run.project["speakers"] = sorted({s["speaker"] for s in segments if s["speaker"] is not None})
    run.project["missing_speaker_segments"] = [s["id"] for s in segments if s["speaker"] is None]
    run.save()
    log("recovered_transcript", segments=segments)


def tempo(ratio):
    factors = []
    while ratio > 4:
        factors.append(4)
        ratio /= 4
    while ratio < .5 - 1e-9:
        factors.append(.5)
        ratio /= .5
    factors.append(ratio)
    return ",".join(f"atempo={f:.6f}" for f in factors)


def synthesize(run):
    segments = read(run.path("translations.json"))["segments"]
    source = {s["id"]: s for s in read(run.path("transcript.json"))["segments"]}
    if len(segments) != len(source) or {s["id"] for s in segments} != set(source):
        raise RuntimeError("Translation coverage mismatch")
    aligned = []
    for s in segments:
        if not s["translated_text"] or any(s[k] != source[s["id"]][k] for k in ["start_ms", "end_ms", "source_text", "speaker"]):
            raise RuntimeError("Translation changed source or has empty text")
        ref = f"voices/{s['id']}.wav"
        if not run.path(ref).exists():
            ff("-i", run.path("separation/vocals.wav"), "-ss", f"{s['start_ms']/1000:.6f}",
               "-to", f"{s['end_ms']/1000:.6f}", "-acodec", "pcm_s16le", run.path(ref))
        url = run.upload(ref)
        stage = f"tts_recovered_{s['id']}"
        result = run.call(stage, "fal-ai/index-tts-2/text-to-speech", {
            "audio_url": url, "prompt": s["translated_text"], "emotional_audio_url": url})
        raw = run.download(result["audio"], f"tts/{s['id']}.wav")
        ap = run.path(f"attempts/{stage}/attempt.json")
        attempt = read(ap)
        attempt["output_artifact"] = str(raw.relative_to(run.root))
        write(ap, attempt)
        duration = float(probe(raw)["format"]["duration"])
        target = (s["end_ms"] - s["start_ms"]) / 1000
        ratio = duration / target
        path = run.path(f"aligned/{s['id']}.wav")
        # Reproduce the legacy atempo-only alignment, including its small duration error.
        ff("-i", raw, "-filter:a", tempo(ratio), "-acodec", "pcm_s16le", path)
        actual = float(probe(path)["format"]["duration"])
        aligned.append({**s, "aligned_artifact": str(path.relative_to(run.root)),
                        "tempo_ratio": ratio, "duration_error_ms": round((actual-target)*1000, 3),
                        "flags": ["extreme_tempo"] if ratio < .75 or ratio > 1.35 else []})
        write(run.path("alignment.json"), {"segments": aligned})
        log("recovered_tts", id=s["id"], ratio=round(ratio, 4), duration_error_ms=aligned[-1]["duration_error_ms"])
    run.project.update(active_alignment="alignment.json", status="synthesized")
    run.save()


def render(run):
    video = run.path("exports/stevejobs_zh-Hans_whisper.mp4")
    if video.exists():
        raise RuntimeError("Export already exists; choose a new run to change parameters")
    segments = read(run.path("alignment.json"))["segments"]
    if len(segments) != len(read(run.path("translations.json"))["segments"]):
        raise RuntimeError("Incomplete speech set")
    vd = float(probe(run.path("source/clip.mp4"))["format"]["duration"])
    inputs = []
    fc = []
    for n, name in enumerate(["separation/background.wav", "separation/vocals.wav"]):
        p = run.path(name)
        inputs.extend(["-i", p])
        duration = float(probe(p)["format"]["duration"])
        tail = f",apad=pad_len={int((vd-duration)*48000)}" if vd > duration else f",atrim=start=0:duration={vd:.6f}"
        vol = ",volume=-100dB" if n else ""
        fc.append(f"[{n}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=mono{tail}{vol}[a{n}]")
    for n, s in enumerate(segments, 2):
        inputs.extend(["-i", run.path(s["aligned_artifact"])])
        fc.append(f"[{n}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=mono,adelay={s['start_ms']}|{s['start_ms']}[a{n}]")
    fc.append("".join(f"[a{n}]" for n in range(len(segments)+2)) +
              f"amix=inputs={len(segments)+2}:duration=longest:normalize=0,alimiter=limit=0.98:attack=2:release=50[out]")
    mix = run.path("mix/final.wav")
    ff(*inputs, "-filter_complex", ";".join(fc), "-map", "[out]", "-t", vd, "-c:a", "pcm_f32le", mix)
    # Float PCM stores the filter output without inserting intermediate integer clipping.
    ff("-i", run.path("source/clip.mp4"), "-i", mix, "-map", "0:v", "-map", "1:a",
       "-t", vd, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", video)
    ff("-i", video, "-f", "null", "-")
    run.project.update(latest_mix="mix/final.wav", latest_export=str(video.relative_to(run.root)),
                       status="exported_with_legacy_duration_tolerance")
    run.save()
    write(run.path("checks.json"), {"full_decode": "passed", "probe": probe(video),
          "expected_segments": len(segments), "actual_segments": len(segments),
          "duration_error_ms": [s["duration_error_ms"] for s in segments],
          "subjective_listening": "user_review_pending"})
    log("recovered_export", artifact=str(video.relative_to(run.root)))


def quality_check(run):
    result = run.call("qc_recovered", "fal-ai/whisper", {
        "audio_url": run.upload(run.project["latest_mix"]),
        **run.project["asr_configuration"]["parameters"]})
    write(run.path("qc/roundtrip_asr.json"), result)
    segments = read(run.path("alignment.json"))["segments"]
    audio_checks = []
    for s in segments:
        audio, rate = sf.read(run.path(s["aligned_artifact"]))
        audio_checks.append({"id": s["id"], "sample_rate": rate, "samples": len(audio),
                             "rms": float(np.sqrt(np.mean(audio*audio))),
                             "peak": float(np.max(np.abs(audio))), "tempo_ratio": s["tempo_ratio"],
                             "duration_error_ms": s["duration_error_ms"]})
    frame_hashes = {}
    for name in ["source/clip.mp4", run.project["latest_export"]]:
        frame_hashes[name] = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(run.path(name)), "-map", "0:v:0",
            "-f", "hash", "-hash", "sha256", "-"], text=True).strip()
    checks = read(run.path("checks.json"))
    checks.update(audio=audio_checks, all_non_silent=all(s["rms"]>1e-5 for s in audio_checks),
                  frame_hashes=frame_hashes, identical_picture=len(set(frame_hashes.values()))==1,
                  source_hash_matches=digest(run.path(run.project["source"]))==run.project["source_sha256"],
                  max_abs_duration_error_ms=max(abs(s["duration_error_ms"]) for s in audio_checks),
                  detected_languages=result.get("inferred_languages", result.get("languages")))
    write(run.path("checks.json"), checks)
    log("recovered_qc", identical_picture=checks["identical_picture"],
        max_abs_duration_error_ms=checks["max_abs_duration_error_ms"], text=result.get("text", ""))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["prepare", "separate", "asr", "tts", "render", "qc", "billing"])
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--baseline", type=Path)
    p.add_argument("--separation", choices=["demucs", "sam"])
    p.add_argument("--credentials", type=Path)
    args = p.parse_args()
    if args.credentials:
        load_dotenv(args.credentials)
    if args.command == "prepare":
        if args.baseline is None or args.separation is None:
            p.error("prepare needs --baseline and explicit --separation")
        prepare(args.run.resolve(), args.baseline.resolve(), args.separation)
    else:
        run = Run(args.run)
        {"separate": separate, "asr": transcribe, "tts": synthesize, "render": render,
         "qc": quality_check, "billing": billing}[args.command](run)


if __name__ == "__main__":
    main()
