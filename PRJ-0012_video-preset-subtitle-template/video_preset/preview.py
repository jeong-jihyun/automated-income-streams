"""ffmpeg 로 샘플 배경에 자막 스타일을 입힌 미리보기 mp4 / GIF."""
import os
import shutil
import subprocess


def have_ass_filter():
    if shutil.which("ffmpeg") is None:
        return False
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return " ass " in out


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "default=nw=1", path],
                       capture_output=True, text=True, check=True).stdout
    d = dict(line.split("=") for line in r.split())
    return {"width": int(d["width"]), "height": int(d["height"]), "duration": float(d["duration"])}


def make_preview(ass_path, out_dir, name, resolution, background, seconds=3.0, gif=True):
    """ass 파일이 있는 폴더에서 실행해 경로 이스케이프 문제를 피한다. (mp4 경로, gif 경로) 반환."""
    os.makedirs(out_dir, exist_ok=True)
    w, h = resolution
    mp4 = os.path.abspath(os.path.join(out_dir, f"{name}.mp4"))
    cwd, ass_name = os.path.dirname(os.path.abspath(ass_path)), os.path.basename(ass_path)
    src = f"color=c=0x{background.lstrip('#')}:s={w}x{h}:d={seconds}:r=25"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src, "-vf", f"ass={ass_name}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", mp4], cwd=cwd, check=True)
    gif_path = None
    if gif:
        gif_path = os.path.abspath(os.path.join(out_dir, f"{name}.gif"))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf",
                        "fps=10,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse",
                        gif_path], check=True)
    return mp4, gif_path
