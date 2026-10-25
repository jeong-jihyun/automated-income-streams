"""자막 파일(SRT·VTT)을 (시작초, 끝초, 글) 목록으로 읽는다."""
import re


class VideoError(ValueError):
    pass


TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})")


def _sec(h, m, s, ms):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        for i, l in enumerate(lines):
            m = TIME.search(l)
            if m:
                g = m.groups(); a, b = _sec(*g[0:4]), _sec(*g[4:8])
                body = re.sub(r"<[^>]+>|\{[^}]+\}", "", " ".join(lines[i + 1:])).strip()
                if body and b > a: cues.append((a, b, body))
                break
    if not cues: raise VideoError("자막에서 시간·글을 찾지 못했습니다(SRT 또는 VTT 형식인지 확인)")
    return sorted(cues)
