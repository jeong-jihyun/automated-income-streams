"""라이브 방송 자막(SRT)에서 상품 홍보용 짧은 클립 구간을 고르고 ffmpeg로 잘라 낸다(세로 9:16 변환 선택). 영상 내용은 분석하지 않고 자막만 본다."""
import re, subprocess, shutil, json, os

MIN_LEN, MAX_LEN = 15.0, 45.0
PRICE = re.compile(r"\d[\d,]*\s*원|할인|특가|쿠폰|무료배송|증정|사은품")
CTA = re.compile(r"링크|구매|주문|장바구니|지금|마감|한정|남았")
BAD = ["무조건", "100%", "최저가", "1위", "완치", "기적"]
TS = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


class ClipError(ValueError):
    pass


def secs(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def parse_srt(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = block.strip().split("\n")
        for i, ln in enumerate(lines):
            m = TS.search(ln)
            if m:
                g = m.groups(); cues.append({"start": secs(*g[:4]), "end": secs(*g[4:]), "text": " ".join(lines[i + 1:]).strip()}); break
    if not cues: raise ClipError("자막에서 시간 구간을 찾지 못했어요")
    for c in cues:
        if c["end"] <= c["start"]: raise ClipError(f"자막 시간이 거꾸로예요: {c}")
    return sorted(cues, key=lambda c: c["start"])


def score(text, keywords):
    s = 0.0
    s += 3 * sum(1 for k in keywords if k in text); s += 2 * len(PRICE.findall(text)); s += 1.5 * len(CTA.findall(text))
    return s


def candidates(cues, keywords, min_len=MIN_LEN, max_len=MAX_LEN):
    out = []
    for i in range(len(cues)):
        for j in range(i, len(cues)):
            st, en = cues[i]["start"], cues[j]["end"]; L = en - st
            if L > max_len: break
            if L < min_len: continue
            txt = " ".join(c["text"] for c in cues[i:j + 1]); sc = score(txt, keywords)
            if sc > 0: out.append({"start": st, "end": en, "len": round(L, 1), "score": round(sc / (L ** 0.5), 2), "text": txt})
    return out


def pick(cues, keywords, top=3, min_len=MIN_LEN, max_len=MAX_LEN):
    chosen = []
    for c in sorted(candidates(cues, keywords, min_len, max_len), key=lambda c: (-c["score"], c["start"])):
        if all(c["end"] <= x["start"] or c["start"] >= x["end"] for x in chosen): chosen.append(c)
        if len(chosen) == top: break
    for c in chosen: c["flags"] = [f"과장 표현 '{w}'" for w in BAD if w in c["text"]]
    return sorted(chosen, key=lambda c: c["start"])


def cut(video, clip, out, vertical=False):
    if not shutil.which("ffmpeg"): raise ClipError("ffmpeg가 없어요")
    vf = ["-vf", "crop=ih*9/16:ih,scale=1080:1920"] if vertical else []
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{clip['start']:.3f}", "-t", f"{clip['end'] - clip['start']:.3f}", "-i", video, *vf, "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-pix_fmt", "yuv420p", out], capture_output=True, text=True)
    if r.returncode: raise ClipError("ffmpeg 오류: " + r.stderr[-200:])
    return out


def srt_for(clip, cues):
    """잘라 낸 클립 기준(0초 시작)으로 자막을 다시 만든다."""
    def ts(x): ms = int(round(x * 1000)); return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    rows = [c for c in cues if c["end"] > clip["start"] and c["start"] < clip["end"]]
    return "\n".join(f"{i}\n{ts(max(0, c['start'] - clip['start']))} --> {ts(min(clip['end'], c['end']) - clip['start'])}\n{c['text']}\n" for i, c in enumerate(rows, 1))
