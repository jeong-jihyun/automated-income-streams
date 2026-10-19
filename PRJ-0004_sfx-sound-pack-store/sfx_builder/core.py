"""ffmpeg로 무음 제거·음량 맞춤·WAV 변환, 파일명 정리, 목록 CSV, 설명 초안, 품질 검사."""
import csv, json, re, subprocess, shutil, wave, struct
from pathlib import Path

AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aiff", ".aif"}
BANNED = ["disney", "marvel", "pokemon", "nintendo", "star wars", "best ever", "100% free"]


def load_settings(path=None):
    p = Path(path) if path else Path(__file__).with_name("settings.json")
    return json.loads(p.read_text(encoding="utf-8"))


def need_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg가 설치되어 있지 않습니다. 먼저 ffmpeg를 설치하세요.")


def list_audio(folder):
    f = Path(folder)
    if not f.is_dir():
        raise NotADirectoryError(f"폴더가 아닙니다: {folder}")
    return sorted(p for p in f.iterdir() if p.suffix.lower() in AUDIO_EXT)


def safe_name(stem, prefix, idx):
    s = re.sub(r"[^0-9A-Za-z]+", "_", stem).strip("_").lower() or "sound"
    return f"{prefix}_{idx:02d}_{s}.wav"


def process_file(src, dst, st):
    """무음 자르기(앞뒤) + 음량 맞춤 + 16비트 WAV 변환."""
    thr = st["silence_threshold_db"]
    trim = (f"silenceremove=start_periods=1:start_threshold={thr}dB,areverse,"
            f"silenceremove=start_periods=1:start_threshold={thr}dB,areverse")
    flt = f"{trim},loudnorm=I={st['target_lufs']}:TP=-1.5:LRA=11"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", flt,
           "-ar", str(st["sample_rate"]), "-c:a", "pcm_s16le", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"변환 실패 {Path(src).name}: {r.stderr.strip()[:200]}")


def wav_info(path):
    with wave.open(str(path), "rb") as w:
        n, rate, ch, width = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    peak = 0
    if width == 2 and n:
        vals = struct.unpack("<" + "h" * (len(raw) // 2), raw)
        peak = max(abs(v) for v in vals)
    import math
    peak_db = 20 * math.log10(peak / 32768) if peak else -120.0
    return {"seconds": round(n / rate, 3) if rate else 0, "rate": rate, "channels": ch, "bits": width * 8, "peak_db": round(peak_db, 2)}


def quality_issues(info, st):
    out = []
    if info["seconds"] < 0.05:
        out.append("너무 짧음(잘렸을 수 있음)")
    if info["peak_db"] < st["min_peak_db"]:
        out.append("소리가 너무 작음")
    if info["peak_db"] >= st["clip_peak_db"]:
        out.append("클리핑 위험")
    return out


def build_pack(src_dir, out_dir, prefix="sfx", settings=None):
    need_ffmpeg()
    st = settings or load_settings()
    out = Path(out_dir)
    wavs = out / "wav"
    wavs.mkdir(parents=True, exist_ok=True)
    rows, skipped = [], []
    files = list_audio(src_dir)
    for i, p in enumerate(files, 1):
        dst = wavs / safe_name(p.stem, prefix, i)
        try:
            process_file(p, dst, st)
        except RuntimeError as e:
            skipped.append((p.name, str(e)))
            continue
        info = wav_info(dst)
        rows.append({"file": dst.name, "source": p.name, **info, "issues": "; ".join(quality_issues(info, st)), "tag_candidates": ", ".join(tag_candidates(p.stem))})
    if rows:
        with open(out / "list.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return {"rows": rows, "skipped": skipped}


def tag_candidates(stem):
    words = [w for w in re.split(r"[^0-9A-Za-z가-힣]+", stem.lower()) if len(w) > 1 and not w.isdigit()]
    return words[:6] or ["sfx"]


def description_draft(theme, rows):
    total = sum(r["seconds"] for r in rows)
    text = (f"{theme} sound effects pack: {len(rows)} files, total {total:.1f} sec. "
            f"WAV {rows[0]['rate'] if rows else 44100}Hz 16-bit. Recorded/created by the author.\n"
            "Tags: " + ", ".join(sorted({t for r in rows for t in r['tag_candidates'].split(', ')})[:15]))
    return text, warn_text(text)


def warn_text(text):
    low = text.lower()
    return [f"금지/과장 표현 주의: '{b}'" for b in BANNED if b in low]


def make_demo(pack_wav_dir, demo_path, st=None):
    need_ffmpeg()
    st = st or load_settings()
    files = sorted(Path(pack_wav_dir).glob("*.wav"))
    if not files:
        raise ValueError("데모를 만들 WAV가 없습니다")
    lst = Path(demo_path).with_suffix(".txt")
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in files), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-t", str(st["demo_seconds"]), "-c:a", "libmp3lame", str(demo_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    lst.unlink(missing_ok=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:200])
