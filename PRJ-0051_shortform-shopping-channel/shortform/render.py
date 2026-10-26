"""장면표로 무음 세로 영상(mp4, 1080x1920)을 만든다. Pillow로 장면 그림을 그리고 ffmpeg로 이어 붙인다. 글꼴 파일이 있어야 한다."""
import os, shutil, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

FONTS = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
W, H = 1080, 1920


class RenderError(RuntimeError):
    pass


def find_font(path=None):
    for f in ([path] if path else []) + FONTS:
        if f and os.path.exists(f): return f
    raise RenderError("한글 글꼴 파일을 찾지 못했어요(--font 로 지정하세요)")


def wrap(draw, text, font, width):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > width and cur: lines.append(cur); cur = ch
        else: cur += ch
    return lines + [cur]


def frame(scene, font_path, idx, total):
    im = Image.new("RGB", (W, H), (28, 32, 48)); d = ImageDraw.Draw(im)
    big, small = ImageFont.truetype(font_path, 84), ImageFont.truetype(font_path, 48)
    y = 640
    for i, line in enumerate(scene["screen"]):
        f = small if i == 0 and line.startswith("광고") else big
        for ln in wrap(d, line, f, W - 160):
            d.text((80, y), ln, font=f, fill=(255, 214, 90) if f is small else (255, 255, 255)); y += f.size + 20
        y += 30
    d.rectangle((80, H - 160, 80 + int((W - 160) * (idx + 1) / total), H - 140), fill=(255, 214, 90))
    return im


def render(plan, out, font=None):
    if not shutil.which("ffmpeg"): raise RenderError("ffmpeg가 없어요")
    fp = find_font(font)
    with tempfile.TemporaryDirectory() as td:
        lst = []
        for i, s in enumerate(plan["scenes"]):
            p = os.path.join(td, f"s{i}.png"); frame(s, fp, i, len(plan["scenes"])).save(p); lst += [f"file '{p}'", f"duration {s['dur']}"]
        lst.append(f"file '{os.path.join(td, 's%d.png' % (len(plan['scenes']) - 1))}'")
        open(os.path.join(td, "list.txt"), "w").write("\n".join(lst))
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(td, "list.txt"), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-movflags", "+faststart", out], capture_output=True, text=True)
        if r.returncode: raise RenderError("ffmpeg 오류: " + r.stderr[-200:])
    return out
