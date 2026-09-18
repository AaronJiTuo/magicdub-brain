"""Offline comparison artifacts; waveform measurements are not listening verdicts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from compare import ROOT, read, write

RATE = 48000
FRAMES = RATE * 60
MODELS = [("demucs", "Demucs"), ("sam1", "SAM 时间段 1 候选"),
          ("sam3", "SAM 时间段 3 候选"), ("baseline1", "SAM 文字基线"),
          ("pcm24", "SAM 文字 · PCM24 输入")]


def audio(path, full=True):
    info = sf.info(path)
    if info.channels not in (1, 2):
        raise ValueError("Unexpected channel count")
    layout = "pan=stereo|c0=c0|c1=c0" if info.channels == 1 else "anull"
    filters = f"aresample={RATE}:filter_size=64:phase_shift=10:exact_rational=1,{layout}"
    if full:
        filters += ",apad,atrim=duration=60"
    pcm = subprocess.check_output(["ffmpeg", "-hide_banner", "-v", "error", "-xerror",
                                   "-i", str(path), "-af", filters, "-f", "f32le", "-"])
    return np.frombuffer(pcm, dtype="<f4").reshape(-1, 2).copy()


def rms(x):
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))


def metric(x, original, start, end):
    a, b = int(start * RATE), int(end * RATE)
    y, ref = x[a:b], original[a:b]
    corr = float(np.corrcoef(y.ravel(), ref.ravel())[0, 1]) if np.std(y) > 1e-10 and np.std(ref) > 1e-10 else None
    return {"rms": rms(y), "rms_relative_original_db": float(20 * np.log10((rms(y) + 1e-12) / (rms(ref) + 1e-12))),
            "correlation_original": corr,
            "side_rms": rms((y[:, 0] - y[:, 1]) / 2)}


def main():
    config = read(ROOT / "experiment.json")
    outputs = ROOT / "review"
    outputs.mkdir(exist_ok=True)
    original = audio(ROOT / "original.wav")
    source = Path(config["source_project"])
    # Confirm identical decoded input to the corresponding prefix of the accepted project.
    ref, sr = sf.read(source / "source/audio.wav", frames=44100 * 60, dtype="float32", always_2d=True)
    inp, inp_sr = sf.read(ROOT / "original.wav", dtype="float32", always_2d=True)
    assert sr == inp_sr == 44100 and np.array_equal(ref, inp)
    tts = np.zeros((FRAMES, 2), dtype=np.float32)
    reused = []
    for s in read(source / "alignment.json")["segments"]:
        offset = round(s["start_ms"] * RATE / 1000)
        if offset >= FRAMES:
            continue
        x = audio(source / s["aligned_artifact"], full=False)
        count = min(len(x), FRAMES - offset)
        tts[offset:offset + count] += x[:count]
        reused.append(s["id"])
    preserve = np.zeros(FRAMES, dtype=np.float32)
    fade = round(0.04 * RATE)
    for w in config["preserve_original_windows"]:
        a, b = round(w["start"] * RATE), round(w["end"] * RATE)
        preserve[a:b] = 1
        preserve[a:a + fade] = np.linspace(0, 1, fade)
        preserve[b - fade:b] = np.linspace(1, 0, fade)
    arrays = {"original": original, "tts_reference": tts}
    labels = {"original": "原始英文现场音", "tts_reference": "复用的中文配音（无背景）"}
    native = {}
    tested = [(name, label) for name, label in MODELS if (ROOT / name / "result.json").exists()]
    for name, label in tested:
        f = ROOT / name / ("vocals.wav" if name == "demucs" else "target.wav")
        i = sf.info(f)
        if abs(i.duration - 60) > 0.15:
            raise ValueError(f"{name}: duration mismatch {i.duration}")
        native[name] = {"sample_rate": i.samplerate, "channels": i.channels, "subtype": i.subtype,
                        "duration_seconds": i.duration, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
        target = audio(f)
        background = original - target
        keep = background * (1 - preserve[:, None]) + original * preserve[:, None]
        for kind, x, title in [("target", target, "提取人声"), ("background", background, "原音减人声"),
                               ("keep", keep, "背景＋26.8–28.2 秒原音示范"),
                               ("dub", background + tts, "中文配音＋相减背景"),
                               ("dub_keep", keep + tts, "中文配音＋局部原音示范")]:
            arrays[name + "_" + kind] = x
            labels[name + "_" + kind] = label + " · " + title
        if name != "demucs":
            residual = audio(ROOT / name / "residual.wav")
            arrays[name + "_residual"] = residual
            labels[name + "_residual"] = label + " · 模型直接输出的背景"
            arrays[name + "_residual_dub"] = residual + tts
            labels[name + "_residual_dub"] = label + " · 中文配音＋模型背景"
    # One gain for EVERY playable comparison, avoiding independent loudness normalization.
    peak = max(float(np.max(np.abs(x))) for x in arrays.values())
    gain = min(1.0, 0.95 / peak)
    reports = {}
    tracks = []
    for key, x in arrays.items():
        assert x.shape == (FRAMES, 2) and np.isfinite(x).all()
        dest = outputs / (key + ".wav")
        sf.write(dest, x * gain, RATE, subtype="FLOAT")
        preview = outputs / (key + ".flac")
        sf.write(preview, x * gain, RATE, subtype="PCM_24")
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-xerror", "-i", str(dest),
                        "-f", "null", "-"], check=True)
        reports[key] = {"pre_gain_peak": float(np.max(np.abs(x))), "rms": rms(x),
                        "windows": {w["name"]: metric(x, original, w["start"], w["end"])
                                    for w in config["listening_windows"]}}
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-xerror", "-i", str(preview),
                        "-f", "null", "-"], check=True)
        tracks.append({"key": key, "label": labels[key], "url": preview.name, "float_wav": dest.name})
    for name, _ in tested:
        # Preservation demo must exactly match original over its flat interior.
        a, b = round(26.84 * RATE), round(28.16 * RATE)
        assert np.array_equal(arrays[name + "_keep"][a:b], original[a:b])
    data = {"source": config["sample"], "sample_seconds": 60, "tracks": tracks,
            "model_labels": dict(tested),
            "windows": config["listening_windows"], "native_outputs": native,
            "common_gain": gain, "reused_tts_segments": reused,
            "input_matches_cached_original_prefix": True,
            "qc": {"all_outputs_full_decode": True, "finite": True, "same_duration": True},
            "limitations": ["时间窗按已转写内容定位，观众笑声与重叠区域的类别须试听确认。",
                            "局部原音保留是固定时间窗示范，不是自动检测能力；需要检查英文残留。",
                            "所有播放文件使用同一增益，未分别归一化；SAM 原生声道数以表格为准。",
                            "本页复用旧中文配音，只比较分离与混音；没有重新翻译、TTS 或 QA。"],
            "measurements": reports}
    data["quality_findings"] = {}
    for name, _ in tested:
        target_level = reports[name + "_target"]["windows"]["讲话参考"]["rms_relative_original_db"]
        background = reports[name + "_background"]["windows"]["讲话参考"]
        data["quality_findings"][name] = {
            "speech_reference_target_relative_db": target_level,
            "background_correlation_with_original_speech": background["correlation_original"],
            "target_near_silent_on_transcribed_speech": target_level < -35,
            "requires_audition": True}
    data["input_stereo"] = {"lr_correlation": float(np.corrcoef(original[:, 0], original[:, 1])[0, 1]),
                            "side_rms": rms((original[:, 0] - original[:, 1]) / 2)}
    data["limitations"].append("本样片两声道高度相似，不足以验证宽立体声或复杂声场。")
    if (ROOT / "costs.json").exists():
        data["costs"] = read(ROOT / "costs.json")
    write(ROOT / "analysis.json", data)
    write(outputs / "data.json", data)
    (outputs / "index.html").write_text((Path(__file__).parent / "review.html").read_text())
    print(json.dumps({"outputs": len(tracks), "common_gain": gain, "native_outputs": native,
                      "qc": data["qc"], "page": str(outputs / "index.html")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
