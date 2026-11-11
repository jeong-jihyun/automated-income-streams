"""사용자가 준 종가 CSV로 단순 전략을 과거에 돌려 보는 도구. 미래 가격을 보지 않도록 신호는 다음 날 종가에 체결."""
import csv, datetime as dt, math

MIN_ROWS = 60


def load(path):
    rows, prev = [], None
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            try:
                d = dt.date.fromisoformat(r["date"].strip()); c = float(r["close"])
            except (ValueError, KeyError): raise ValueError(f"{i}행: 날짜 또는 종가 형식 오류")
            if c <= 0: raise ValueError(f"{i}행: 종가는 0보다 커야 합니다")
            if prev and d <= prev: raise ValueError(f"{i}행: 날짜가 오름차순이 아니거나 중복입니다")
            rows.append((d, c)); prev = d
    if len(rows) < MIN_ROWS: raise ValueError(f"데이터가 {len(rows)}줄뿐입니다 (최소 {MIN_ROWS}줄 필요)")
    return rows


def warnings(rows):
    w = []
    for (d0, c0), (d1, c1) in zip(rows, rows[1:]):
        if (d1 - d0).days > 10: w.append(f"{d0}~{d1} 사이 {(d1 - d0).days}일 빠진 구간")
        if abs(c1 / c0 - 1) > 0.4: w.append(f"{d1} 하루 변동 {c1 / c0 - 1:+.0%} - 분할·오류 가능성")
    return w


def sma(vals, n, i):
    return None if i + 1 < n else sum(vals[i + 1 - n:i + 1]) / n


class Acct:
    def __init__(self, cash, fee, slip):
        self.cash, self.sh, self.fee, self.slip, self.trades, self.invested = cash, 0.0, fee, slip, 0, cash

    def buy_value(self, price, value):
        value = min(value, self.cash / (1 + self.fee))
        if value <= 0: return
        px = price * (1 + self.slip); q = value / px
        self.cash -= value * (1 + self.fee); self.sh += q; self.trades += 1

    def sell_all(self, price):
        if self.sh <= 0: return
        self.cash += self.sh * price * (1 - self.slip) * (1 - self.fee); self.sh = 0.0; self.trades += 1

    def equity(self, price): return self.cash + self.sh * price


def run(rows, strategy="buyhold", cash=10_000_000, fee=0.00015, slip=0.0005, monthly=0, fast=20, slow=60):
    if strategy not in ("buyhold", "dca", "sma"): raise ValueError("전략은 buyhold, dca, sma 중 하나")
    if strategy == "sma" and not 1 <= fast < slow: raise ValueError("fast는 1 이상이고 slow보다 작아야 합니다")
    if strategy == "dca" and monthly <= 0: raise ValueError("dca는 월 적립액(monthly)이 필요합니다")
    closes = [c for _, c in rows]
    a = Acct(0 if strategy == "dca" else cash, fee, slip); curve = []; want = False; last_month = None
    for i, (d, c) in enumerate(rows):
        if strategy == "buyhold" and i == 0: a.buy_value(c, a.cash)
        elif strategy == "dca" and (d.year, d.month) != last_month:
            a.cash += monthly; a.invested += monthly; a.buy_value(c, a.cash); last_month = (d.year, d.month)
        elif strategy == "sma":
            if want and a.sh == 0: a.buy_value(c, a.cash)           # 어제 신호를 오늘 종가에 체결
            elif not want and a.sh > 0: a.sell_all(c)
            f, s = sma(closes, fast, i), sma(closes, slow, i)
            if f is not None and s is not None: want = f > s         # 오늘 신호는 내일 체결
        curve.append((d, a.equity(c)))
    return curve, a


def metrics(curve, invested):
    vals = [v for _, v in curve]; days = (curve[-1][0] - curve[0][0]).days or 1; yrs = days / 365.25
    peak, mdd = vals[0], 0.0
    for v in vals:
        peak = max(peak, v); mdd = min(mdd, v / peak - 1 if peak > 0 else 0)
    rets = [b / a - 1 for a, b in zip(vals, vals[1:]) if a > 0]
    mean = sum(rets) / len(rets) if rets else 0
    vol = math.sqrt(sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)) * math.sqrt(252) if len(rets) > 1 else 0
    total = vals[-1] / invested - 1 if invested else 0
    cagr = (vals[-1] / invested) ** (1 / yrs) - 1 if yrs >= 1 and invested and vals[-1] > 0 else None
    return {"final": round(vals[-1]), "invested": round(invested), "total_return": total, "cagr": cagr, "mdd": mdd, "vol": vol, "years": round(yrs, 2)}


def compare(rows, **kw):
    out = {}
    for name in ("buyhold", "dca", "sma"):
        k = dict(kw)
        if name == "dca" and not k.get("monthly"): k["monthly"] = k.get("cash", 10_000_000) / 12
        curve, a = run(rows, name, **k); m = metrics(curve, a.invested); m["trades"] = a.trades; out[name] = m
    return out


def text(res, warns):
    names = {"buyhold": "한 번에 사서 보유", "dca": "매월 적립 매수", "sma": "이동평균 교차"}
    L = []
    for k, m in res.items():
        cg = f"{m['cagr']:.1%}" if m["cagr"] is not None else "계산 안 함(1년 미만)"
        L.append(f"{names[k]}: 넣은 돈 {m['invested']:,} → 최종 {m['final']:,} ({m['total_return']:+.1%}), 연환산 {cg}, 최대낙폭 {m['mdd']:.1%}, 변동성 {m['vol']:.1%}, 거래 {m['trades']}번")
    L += ["주의: " + w for w in warns]
    L.append("※ 과거 결과이며 미래를 보장하지 않습니다. 세금·배당·분할 조정은 데이터에 이미 반영된 것만 포함되고, 수수료·슬리피지는 예시값입니다. 투자 조언이 아닙니다.")
    return "\n".join(L)
