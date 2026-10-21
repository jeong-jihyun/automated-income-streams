"""행사 정보 JSON + 사진 → 휴대폰용 초대장 HTML 한 파일 + 캘린더(.ics). 사진은 줄여서 파일 안에 넣는다."""
import base64
import html
import io
import json
import os
import re
from datetime import date, datetime, timedelta
from urllib.parse import quote
from PIL import Image, ImageOps

THEMES = {"rose": ("#FFF5F7", "#B8486B"), "mint": ("#F2FBF7", "#2E8B6F"), "navy": ("#F3F6FB", "#1F3864")}
TEL = re.compile(r"^[0-9+\-\s]{7,20}$")
MAX_PHOTOS = 8


class InviteError(ValueError):
    pass


def load(path):
    try:
        ev = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise InviteError(f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise InviteError(f"JSON 형식 오류: {e}")
    errs = []
    for k in ("title", "date", "time", "place"):
        if not str(ev.get(k, "")).strip():
            errs.append(f"'{k}' 항목이 비었습니다")
    if not errs:
        try:
            ev["_dt"] = datetime.strptime(f"{ev['date']} {ev['time']}", "%Y-%m-%d %H:%M")
        except ValueError:
            errs.append("날짜는 YYYY-MM-DD, 시간은 HH:MM 형식이어야 합니다 (없는 날짜도 안 됩니다)")
    if ev.get("theme", "rose") not in THEMES:
        errs.append(f"theme은 {', '.join(THEMES)} 중 하나")
    if len(ev.get("photos", [])) > MAX_PHOTOS:
        errs.append(f"사진은 최대 {MAX_PHOTOS}장")
    for c in ev.get("contacts", []):
        if not TEL.match(c.get("tel", "")):
            errs.append(f"전화번호 형식 오류: {c.get('tel')}")
    if errs:
        raise InviteError("; ".join(errs))
    return ev


def photo_data_uri(path, max_side=900):
    try:
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    except (FileNotFoundError, OSError):
        raise InviteError(f"사진을 열 수 없습니다: {path}")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def dday_text(ev_date, today):
    d = (ev_date - today).days
    return "오늘입니다" if d == 0 else (f"D-{d}" if d > 0 else f"{-d}일 지났습니다")


def make_ics(ev):
    s = ev["_dt"]; e = s + timedelta(hours=2)
    f = lambda d: d.strftime("%Y%m%dT%H%M%S")
    esc = lambda t: t.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//invitation//KO", "BEGIN:VEVENT",
                        f"DTSTART:{f(s)}", f"DTEND:{f(e)}", f"SUMMARY:{esc(ev['title'])}",
                        f"LOCATION:{esc(ev['place'] + ' ' + ev.get('address', ''))}", "END:VEVENT", "END:VCALENDAR", ""])


def build_html(ev, base_dir, today=None):
    today = today or date.today()
    bg, accent = THEMES[ev.get("theme", "rose")]
    e = html.escape
    photos = "".join(f'<img src="{photo_data_uri(os.path.join(base_dir, p))}" alt="사진 {i + 1}">' for i, p in enumerate(ev.get("photos", [])))
    contacts = "".join(f'<a class="btn" href="tel:{re.sub(r"[^0-9+]", "", c["tel"])}">{e(c["label"])}에게 전화</a>' for c in ev.get("contacts", []))
    greet = "<br>".join(e(l) for l in ev.get("greeting", "").split("\n"))
    q = quote(ev.get("address") or ev["place"])
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(ev['title'])}</title>
<meta property="og:title" content="{e(ev['title'])}">
<style>body{{margin:0;background:{bg};font-family:sans-serif;text-align:center;line-height:1.7}}main{{max-width:480px;margin:auto;padding:24px 16px}}
h1{{color:{accent}}}img{{width:100%;border-radius:8px;margin:8px 0}}.btn{{display:block;margin:8px 0;padding:14px;border-radius:8px;background:{accent};color:#fff;text-decoration:none}}</style></head>
<body><main><h1>{e(ev['title'])}</h1><p>{greet}</p>
<p><b>{e(ev['date'])} {e(ev['time'])}</b> ({dday_text(ev['_dt'].date(), today)})<br>{e(ev['place'])}<br>{e(ev.get('address', ''))}</p>
{photos}
<a class="btn" href="https://map.naver.com/p/search/{q}">네이버 지도에서 보기</a>
<a class="btn" href="invitation.ics">내 달력에 넣기</a>{contacts}</main></body></html>"""


def build(config_path, out_dir, today=None):
    ev = load(config_path)
    os.makedirs(out_dir, exist_ok=True)
    page = build_html(ev, os.path.dirname(os.path.abspath(config_path)), today)
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page)
    open(os.path.join(out_dir, "invitation.ics"), "w", encoding="utf-8", newline="").write(make_ics(ev))
    return {"bytes": len(page.encode("utf-8")), "photos": len(ev.get("photos", []))}
