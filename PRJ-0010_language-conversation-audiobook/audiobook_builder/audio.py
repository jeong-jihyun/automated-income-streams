"""문장별 음성 + 무음 간격 → 챕터 mp3 + 목차."""
import os
import re
import subprocess
import wave
from .tts import write_silence


def wav_seconds(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / w.getframerate()


def safe(name):
    return re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", name).strip("_") or "chapter"


def build_chapter(idx, name, rows, provider, cfg, work_dir, out_dir):
    """문장 wav + 간격을 이어 붙여 챕터 wav 를 만들고 mp3 로 변환. 문장 시작 시각 목록을 돌려준다."""
    rate = cfg["sample_rate"]
    gap = cfg["gap_sec"]
    gap_path = os.path.join(work_dir, "gap.wav")
    write_silence(gap_path, gap, rate)
    wav_out = os.path.join(work_dir, f"ch{idx:02d}.wav")
    starts, t = [], 0.0
    with wave.open(wav_out, "wb") as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
        for r in rows:
            p = os.path.join(work_dir, f"s{r['no']}.wav")
            provider.synth(r, p)
            with wave.open(p, "rb") as w:
                if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (rate, 1, 2):
                    raise ValueError(f"{r['no']}번 음성 형식이 설정과 다릅니다")
                frames = w.readframes(w.getnframes()); dur = w.getnframes() / rate
            starts.append(round(t, 2))
            out.writeframes(frames)
            with wave.open(gap_path, "rb") as g:
                out.writeframes(g.readframes(g.getnframes()))
            t += dur + gap
    mp3 = os.path.join(out_dir, f"{idx:02d}_{safe(name)}.mp3")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav_out, "-codec:a", "libmp3lame",
                    "-b:a", cfg["mp3_bitrate"], mp3], check=True)
    return {"mp3": mp3, "starts": starts, "seconds": round(t, 2)}


def fmt(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def toc_text(chapter_info):
    lines = ["# 목차"]
    for i, (name, rows, info) in enumerate(chapter_info, start=1):
        lines.append(f"{i}. {name} ({fmt(info['seconds'])}, {len(rows)}문장)")
        for r, s in zip(rows, info["starts"]):
            lines.append(f"   {fmt(s)}  {r['no']}. {r['text']}")
    return "\n".join(lines) + "\n"
