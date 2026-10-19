"""BGM 카탈로그 도구의 핵심 기능: 곡 정보 검증, 미리듣기 생성, 사이트·라이선스 안내문 생성."""
import csv
import html
import os
import re
import shutil
import subprocess

REQUIRED = ["id", "title", "file", "mood", "genre", "bpm",
            "made_by", "tool", "rights_basis", "terms_checked"]
# made_by 가 이 값이면 '도구' 칸과 '약관 확인일'을 반드시 적어야 한다.
AI_VALUES = ("ai", "AI")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PREVIEW_SECONDS = 30


def read_rows(csv_path):
    """CSV 를 읽어 (열 이름 목록, 행 목록)을 돌려준다. 비어 있으면 ValueError."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"곡 정보 CSV가 없습니다: {csv_path}")
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [{k: (v or "").strip() for k, v in r.items() if k} for r in reader]
        cols = reader.fieldnames or []
    if not rows:
        raise ValueError("곡 정보 CSV에 곡이 한 줄도 없습니다.")
    return cols, rows


def validate(cols, rows, music_dir):
    """문제 목록을 돌려준다. 빈 리스트면 통과. 각 항목은 (행번호, 곡ID, 내용)."""
    problems = []
    missing_cols = [c for c in REQUIRED if c not in cols]
    if missing_cols:
        return [(0, "", f"필수 열이 없습니다: {', '.join(missing_cols)}")]
    seen = {}
    for i, r in enumerate(rows, start=2):  # 1행은 제목줄
        tid = r["id"]
        if not tid:
            problems.append((i, tid, "곡 ID가 비어 있습니다"))
        elif tid in seen:
            problems.append((i, tid, f"곡 ID가 {seen[tid]}행과 겹칩니다"))
        else:
            seen[tid] = i
        for c in ("title", "file", "mood", "genre", "made_by"):
            if not r[c]:
                problems.append((i, tid, f"'{c}' 칸이 비어 있습니다"))
        if not r["rights_basis"]:
            problems.append((i, tid, "권리 근거가 비어 있습니다 (직접 작곡, 도구 약관 등을 적어야 합니다)"))
        if r["made_by"] in AI_VALUES:
            if not r["tool"]:
                problems.append((i, tid, "AI로 만든 곡인데 사용한 도구 이름이 없습니다"))
            if not r["terms_checked"]:
                problems.append((i, tid, "AI로 만든 곡인데 약관 확인일이 없습니다"))
        if r["terms_checked"] and not DATE_RE.match(r["terms_checked"]):
            problems.append((i, tid, "약관 확인일은 YYYY-MM-DD 형식이어야 합니다"))
        if r["bpm"]:
            if not r["bpm"].isdigit() or not (30 <= int(r["bpm"]) <= 300):
                problems.append((i, tid, "BPM은 30~300 사이 숫자여야 합니다"))
        else:
            problems.append((i, tid, "BPM이 비어 있습니다"))
        if r["file"] and not os.path.isfile(os.path.join(music_dir, r["file"])):
            problems.append((i, tid, f"음악 파일이 없습니다: {r['file']}"))
    return problems


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def make_preview(src, dst, seconds=PREVIEW_SECONDS):
    """음량을 맞춘 미리듣기 mp3 를 만든다. 곡이 짧으면 곡 길이만큼만 만든다."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg 가 설치되어 있지 않습니다.")
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    total = probe_duration(src)
    length = min(seconds, total)
    fade_start = max(length - 2, 0)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{length:.3f}",
         "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={fade_start:.3f}:d=2",
         "-codec:a", "libmp3lame", "-b:a", "128k", dst],
        check=True)
    return dst


def build_site(rows, out_dir, site_title="BGM 라이브러리"):
    """카탈로그 정적 사이트(index.html)를 만든다. 모든 글자는 HTML 이스케이프한다."""
    os.makedirs(out_dir, exist_ok=True)
    e = html.escape
    cards = []
    for r in rows:
        prev = f"previews/{r['id']}.mp3"
        cards.append(
            "<article class='track'>"
            f"<h2>{e(r['title'])}</h2>"
            f"<p>{e(r['genre'])} · {e(r['mood'])} · {e(r['bpm'])} BPM</p>"
            f"<audio controls preload='none' src='{e(prev, quote=True)}'></audio>"
            "</article>")
    page = (
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{e(site_title)}</title>"
        "<style>body{font-family:sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}"
        ".track{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:1rem 0}"
        "audio{width:100%}</style></head><body>"
        f"<h1>{e(site_title)}</h1><p>총 {len(rows)}곡 · 30초 미리듣기</p>"
        + "".join(cards) +
        "<p><a href='LICENSE_GUIDE.md'>이용 안내(라이선스 초안)</a></p></body></html>")
    path = os.path.join(out_dir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


def license_guide(rows, site_title="BGM 라이브러리"):
    """구독자용 라이선스 안내문 '초안'. 공개 전 전문가 확인이 필요하다."""
    lines = [
        f"# {site_title} 이용 안내 (초안)", "",
        "> 이 문서는 자동 생성된 초안입니다. 공개 전 반드시 전문가의 확인을 받으세요.", "",
        "## 곡별 제작 방법과 권리 근거", "",
        "| 곡 ID | 제목 | 제작 방법 | 도구 | 권리 근거 | 약관 확인일 |",
        "|---|---|---|---|---|---|"]
    for r in rows:
        cells = [r["id"], r["title"], r["made_by"], r["tool"] or "-",
                 r["rights_basis"], r["terms_checked"] or "-"]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    lines += ["", "## 구독자 안내(예시 문구, 수정 필요)", "",
              "- 구독 기간 동안 영상 배경음으로 사용할 수 있습니다.",
              "- 곡 자체를 다시 판매하거나 배포할 수 없습니다.",
              "- 유튜브 Content ID 등록은 하지 마세요."]
    return "\n".join(lines) + "\n"


def run(csv_path, music_dir, out_dir, site_title="BGM 라이브러리", seconds=PREVIEW_SECONDS):
    """전체 흐름. 검증에 실패하면 아무 파일도 만들지 않고 문제 목록만 돌려준다."""
    cols, rows = read_rows(csv_path)
    problems = validate(cols, rows, music_dir)
    if problems:
        return {"ok": False, "problems": problems, "tracks": 0}
    os.makedirs(out_dir, exist_ok=True)
    for r in rows:
        make_preview(os.path.join(music_dir, r["file"]),
                     os.path.join(out_dir, "previews", f"{r['id']}.mp3"), seconds)
    build_site(rows, out_dir, site_title)
    with open(os.path.join(out_dir, "LICENSE_GUIDE.md"), "w", encoding="utf-8") as f:
        f.write(license_guide(rows, site_title))
    return {"ok": True, "problems": [], "tracks": len(rows)}
