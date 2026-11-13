"""팀별 주간 보고 CSV들을 합쳐 한 장짜리 HTML 대시보드(전주 대비, 누락 팀 표시)를 만든다."""
import csv, glob, html, os

COLS = ["team", "week", "metric", "value"]


def read_dir(folder):
    rows, bad = [], []
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise ValueError("CSV 파일이 없습니다: " + folder)
    for path in files:
        with open(path, encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            miss = [c for c in COLS if c not in (rd.fieldnames or [])]
            if miss:
                bad.append((os.path.basename(path), 0, "열이 없습니다: " + ", ".join(miss))); continue
            for n, r in enumerate(rd, start=2):
                try:
                    v = float(r["value"].replace(",", ""))
                    if not r["team"].strip() or not r["metric"].strip() or not r["week"].strip():
                        raise ValueError("빈 칸")
                    rows.append({"team": r["team"].strip(), "week": r["week"].strip(), "metric": r["metric"].strip(), "value": v})
                except (ValueError, AttributeError):
                    bad.append((os.path.basename(path), n, "숫자 또는 빈 칸 오류"))
    return rows, bad


def merge(rows):
    """같은 팀·주·지표가 여러 번 나오면 마지막 값을 쓰고 개수를 센다."""
    d, dup = {}, 0
    for r in rows:
        k = (r["team"], r["week"], r["metric"])
        dup += k in d; d[k] = r["value"]
    return d, dup


def summarize(d, expected_teams=()):
    weeks = sorted({k[1] for k in d}); cur = weeks[-1]; prev = weeks[-2] if len(weeks) > 1 else None
    metrics = sorted({k[2] for k in d}); teams = sorted({k[0] for k in d} | set(expected_teams))
    table = []
    for m in metrics:
        row = {"metric": m, "cells": [], "total": 0.0}
        for t in teams:
            v = d.get((t, cur, m)); p = d.get((t, prev, m)) if prev else None
            chg = None if v is None or p is None or p == 0 else round((v - p) / p * 100, 1)
            row["cells"].append({"team": t, "v": v, "chg": chg}); row["total"] += v or 0
        table.append(row)
    missing = [t for t in teams if all(d.get((t, cur, m)) is None for m in metrics)]
    return {"week": cur, "prev": prev, "teams": teams, "table": table, "missing": missing}


def fmt(v):
    return "-" if v is None else (f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}")


def render(s, bad=()):
    e = html.escape
    head = "".join(f"<th>{e(t)}</th>" for t in s["teams"])
    body = ""
    for r in s["table"]:
        mx = max([c["v"] or 0 for c in r["cells"]] + [1])
        cells = ""
        for c in r["cells"]:
            w = int(100 * (c["v"] or 0) / mx)
            ch = "" if c["chg"] is None else f" <small>({c['chg']:+}%)</small>"
            cells += f'<td>{fmt(c["v"])}{ch}<div style="background:#4a90d9;height:6px;width:{w}%"></div></td>'
        body += f"<tr><th>{e(r['metric'])}</th>{cells}<td><b>{fmt(r['total'])}</b></td></tr>"
    warn = f"<p>⚠ 이번 주 보고가 없는 팀: {e(', '.join(s['missing']))}</p>" if s["missing"] else ""
    skipped = "".join(f"<li>{e(f)} {n}행: {e(w)}</li>" for f, n, w in bad)
    skipped = f"<h3>제외된 줄</h3><ul>{skipped}</ul>" if skipped else ""
    return f"""<!doctype html><html lang="ko"><meta charset="utf-8"><title>주간 보고 대시보드 {e(s['week'])}</title>
<h1>주간 보고 대시보드 — {e(s['week'])}</h1><p>비교 주: {e(s['prev'] or '없음')}</p>{warn}
<table border="1" cellpadding="4"><tr><th>지표</th>{head}<th>합계</th></tr>{body}</table>{skipped}</html>
"""
