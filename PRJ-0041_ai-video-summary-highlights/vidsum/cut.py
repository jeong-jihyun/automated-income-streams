"""하이라이트 구간을 ffmpeg로 잘라 내기. 원본은 건드리지 않고 새 파일로 저장한다."""
import os
import shutil
import subprocess
from .parse import VideoError


def ts(sec):
    return f"{int(sec // 3600):02d}:{int(sec % 3600 // 60):02d}:{sec % 60:06.3f}"


def command(video, h, out):
    return ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{h['start']:.3f}", "-to", f"{h['end']:.3f}", "-i", video, "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", out]


def cut_all(video, hl, out_dir, runner=subprocess.run):
    if not os.path.isfile(video): raise VideoError(f"영상 파일이 없습니다: {video}")
    if shutil.which("ffmpeg") is None and runner is subprocess.run: raise VideoError("ffmpeg가 설치돼 있지 않습니다")
    os.makedirs(out_dir, exist_ok=True); outs = []
    for i, h in enumerate(hl, 1):
        out = os.path.join(out_dir, f"highlight_{i:02d}.mp4")
        r = runner(command(video, h, out), capture_output=True, text=True)
        if getattr(r, "returncode", 0) != 0: raise VideoError(f"자르기 실패(구간 {i}): {(r.stderr or '')[:120]}")
        outs.append(out)
    return outs
