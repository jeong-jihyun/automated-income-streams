"""상품 목록 JSON으로 주제별 추천 정적 사이트(HTML)를 만든다. 상품 정보는 사용자가 넣은 것만 쓰며 쿠팡에서 가져오지 않는다."""
import html, json, os, re
from datetime import date
from urllib.parse import urlparse

DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."  # 문구는 예시. 최신 공식 문구는 직접 확인 필요
ALLOWED_HOSTS = ("link.coupang.com", "coupa.ng")
STALE_DAYS = 7
BAD_WORDS = ["최저가 보장", "무조건", "100%", "1위", "완치", "기적"]


class CurationError(ValueError):
    pass


def load(path):
    try: data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise CurationError(f"상품 파일을 읽지 못했습니다: {e}")
    if not isinstance(data, list): raise CurationError("상품 파일은 목록이어야 합니다")
    return data


def validate(p, today):
    errs = []
    for k in ("id", "name", "topic", "url"):
        if not p.get(k): errs.append(f"'{k}' 없음")
    u = urlparse(p.get("url", ""))
    if p.get("url") and (u.scheme != "https" or u.hostname not in ALLOWED_HOSTS): errs.append("제휴 링크가 아니에요(https://link.coupang.com/… 형태만 허용)")
    for k in ("name", "note"):
        for w in BAD_WORDS:
            if w in (p.get(k) or ""): errs.append(f"과장·보장 표현 '{w}'")
    if p.get("price") is not None and (not isinstance(p["price"], int) or p["price"] <= 0): errs.append("가격이 올바르지 않음")
    if p.get("price") is not None and not p.get("price_date"): errs.append("가격을 적었다면 확인한 날짜(price_date)도 필요")
    return errs


def price_text(p, today):
    if p.get("price") is None: return "가격은 판매 페이지에서 확인하세요"
    d = (today - date.fromisoformat(p["price_date"])).days
    if d > STALE_DAYS: return f"가격 확인 필요 ({d}일 전 확인한 가격은 표시하지 않아요)"
    return f"{p['price']:,}원 ({p['price_date']} 확인 · 변동될 수 있음)"


def card(p, today):
    e = html.escape
    li = lambda xs, c: "".join(f'<li class="{c}">{e(x)}</li>' for x in xs or [])
    return (f'<article><h3>{e(p["name"])}</h3><p class="price">{e(price_text(p, today))}</p><ul>{li(p.get("pros"), "pro")}{li(p.get("cons"), "con")}</ul>'
            f'<p>{e(p.get("note", ""))}</p><a href="{e(p["url"])}" rel="sponsored nofollow noopener" target="_blank">쿠팡에서 보기</a></article>')


def page(title, body):
    return (f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>'
            f'<style>body{{font-family:sans-serif;max-width:720px;margin:auto;padding:16px}}.disc{{background:#fff3cd;padding:8px;border-radius:6px}}article{{border:1px solid #ddd;border-radius:8px;padding:12px;margin:12px 0}}.con{{color:#a33}}</style>'
            f'<p class="disc">{html.escape(DISCLOSURE)}</p><h1>{html.escape(title)}</h1>{body}<footer><p class="disc">{html.escape(DISCLOSURE)}</p></footer></html>')


def slug(t):
    return re.sub(r"[^0-9a-z가-힣]+", "-", t.lower()).strip("-") or "topic"


def build(products, out, today=None):
    today = today or date.today(); ok, bad = [], []
    for p in products:
        errs = validate(p, today); (bad.append({"id": p.get("id", "?"), "errors": errs}) if errs else ok.append(p))
    topics = {}
    for p in ok: topics.setdefault(p["topic"], []).append(p)
    os.makedirs(out, exist_ok=True)
    for t, ps in topics.items():
        ps.sort(key=lambda p: (p.get("price") is None, p.get("price") or 0))
        open(os.path.join(out, slug(t) + ".html"), "w", encoding="utf-8").write(page(f"{t} 추천", "".join(card(p, today) for p in ps)))
    idx = "".join(f'<li><a href="{slug(t)}.html">{html.escape(t)}</a> ({len(ps)}개)</li>' for t, ps in topics.items())
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page("주제별 추천 목록", f"<ul>{idx}</ul>"))
    return {"pages": len(topics) + 1, "included": len(ok), "rejected": bad}
