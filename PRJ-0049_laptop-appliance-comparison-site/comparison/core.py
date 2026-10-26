"""스펙 비교표(HTML)와 가격 기록 추적. 데이터는 사용자가 넣은 것만 쓴다(수집 없음)."""
import csv, html, json, os
from datetime import date

DISCLOSURE = "이 페이지의 링크는 제휴 링크일 수 있으며 구매 시 수수료를 받을 수 있습니다."  # 예시 문구
STALE_DAYS = 7


class CompareError(ValueError):
    pass


def load_products(path):
    try: d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise CompareError(f"상품 파일을 읽지 못했습니다: {e}")
    if not d.get("products") or not d.get("criteria"): raise CompareError("products와 criteria가 필요합니다")
    for k, v in d["criteria"].items():
        if v not in ("higher", "lower", "info"): raise CompareError(f"criteria '{k}'는 higher/lower/info 중 하나여야 합니다")
    return d


def load_history(path):
    h = {}
    if not os.path.exists(path): return h
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        try: h.setdefault(r["id"], []).append((date.fromisoformat(r["date"]), int(r["price"])))
        except (KeyError, ValueError): raise CompareError(f"가격 기록 형식 오류: {r}")
    for v in h.values(): v.sort()
    return h


def add_price(path, pid, day, price):
    if price <= 0: raise CompareError("가격은 0보다 커야 합니다")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new: w.writerow(["id", "date", "price"])
        w.writerow([pid, day.isoformat(), price])


def price_status(hist, today):
    """반환: 현재가(마지막 기록), 최저가, 변동률, 오래됨 여부, 알림."""
    if not hist: return {"current": None, "stale": True, "alert": None}
    cur_d, cur = hist[-1]; low = min(p for _, p in hist); prev = hist[-2][1] if len(hist) > 1 else None
    st = {"current": cur, "date": cur_d, "lowest": low, "stale": (today - cur_d).days > STALE_DAYS, "change_pct": round((cur - prev) / prev * 100, 1) if prev else None, "alert": None}
    if len(hist) >= 3 and cur <= low and cur < max(p for _, p in hist): st["alert"] = "기록 중 최저가예요"
    elif st["change_pct"] is not None and st["change_pct"] <= -10: st["alert"] = f"직전보다 {abs(st['change_pct'])}% 내렸어요"
    return st


def best_cells(products, criteria):
    best = {}
    for k, rule in criteria.items():
        vals = [(p["specs"].get(k), p["id"]) for p in products if isinstance(p["specs"].get(k), (int, float)) and not isinstance(p["specs"].get(k), bool)]
        if rule == "info" or len(vals) < 2: continue
        t = max(v for v, _ in vals) if rule == "higher" else min(v for v, _ in vals)
        best[k] = {i for v, i in vals if v == t}
    return best


def render(data, history, today):
    e, ps, cr = html.escape, data["products"], data["criteria"]
    best = best_cells(ps, cr); st = {p["id"]: price_status(history.get(p["id"], []), today) for p in ps}
    head = "<tr><th></th>" + "".join(f"<th>{e(p['name'])}</th>" for p in ps) + "</tr>"
    rows = []
    for k in cr:
        cells = "".join(f'<td{" class=best" if p["id"] in best.get(k, set()) else ""}>{e(str(p["specs"].get(k, "정보 없음")))}</td>' for p in ps)
        rows.append(f"<tr><th>{e(k)}</th>{cells}</tr>")
    def pc(p):
        s = st[p["id"]]
        if s["current"] is None: return "<td>가격 기록 없음</td>"
        if s["stale"]: return f"<td>가격 확인 필요 ({(today - s['date']).days}일 전 기록)</td>"
        return f"<td>{s['current']:,}원 <small>({s['date']} 기준 · 최저 {s['lowest']:,}원)</small>" + (f" <b>{e(s['alert'])}</b>" if s["alert"] else "") + "</td>"
    rows.append("<tr><th>가격</th>" + "".join(pc(p) for p in ps) + "</tr>")
    return (f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(data.get("title", "비교표"))}</title>'
            f'<style>body{{font-family:sans-serif;padding:12px}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px}}.best{{background:#d9f2d9}}.d{{background:#fff3cd;padding:8px}}</style>'
            f'<p class="d">{e(DISCLOSURE)}</p><h1>{e(data.get("title", "비교표"))}</h1><div style="overflow-x:auto"><table>{head}{"".join(rows)}</table></div>'
            f'<p>초록색 칸은 해당 항목에서 가장 좋은 값입니다. 가격·스펙은 입력된 자료 기준이며 판매처에서 다시 확인하세요.</p></html>')
