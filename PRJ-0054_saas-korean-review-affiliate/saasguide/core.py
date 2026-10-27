"""해외 SaaS 한국어 가이드 글 초안과 점검. 직접 써 본 기능만 다루고, 달러 가격은 환율·확인일과 함께 원화로 환산한다. 제휴 링크 고지를 항상 넣는다."""
import json
import re
from datetime import date

DISCLOSURE = "※ 이 글에는 제휴 링크가 포함되어 있으며, 링크로 가입하시면 제가 수수료를 받을 수 있습니다(가격 변화 없음 여부는 서비스별로 다릅니다)."  # 예시 문구
BAD = ["무조건", "100%", "최고의", "역대급", "완벽", "평생 무료"]
STALE_DAYS = 30


class GuideError(ValueError):
    pass


def load(path):
    try: return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise GuideError(f"파일을 읽지 못했습니다: {e}")


def krw(usd, rate):
    return round(usd * rate, -2)  # 100원 단위로 반올림


def validate(f, today):
    miss = [k for k in ("tool", "affiliate_link", "tested_on", "version_note", "steps") if not f.get(k)]
    if miss: raise GuideError("빠진 항목: " + ", ".join(miss))
    try: t = date.fromisoformat(f["tested_on"])
    except ValueError: raise GuideError("tested_on은 YYYY-MM-DD 형식이어야 해요")
    if t > today: raise GuideError("직접 써 본 날짜(tested_on)가 미래예요")
    if not f.get("cons"): raise GuideError("아쉬운 점(cons)도 1개 이상 필요해요")
    if not f["affiliate_link"].startswith("https://"): raise GuideError("제휴 링크는 https 주소여야 해요")
    for p in f.get("plans", []):
        if p.get("usd_month") is not None and not (f.get("usd_krw_rate") and f.get("rate_date")): raise GuideError("달러 가격을 쓰려면 환율(usd_krw_rate)과 환율 기준일(rate_date)이 필요해요")
    for s in f["steps"]:
        if not s.get("title") or not s.get("how"): raise GuideError("단계마다 title과 how가 필요해요")
    return t


def make(f, today=None):
    today = today or date.today(); t = validate(f, today); age = (today - t).days
    o = [DISCLOSURE, "", f"# {f['tool']} 한국어 시작 가이드", "", f"- 직접 써 본 날: {f['tested_on']} ({f['version_note']})"]
    if age > STALE_DAYS: o.append(f"- ⚠ 확인한 지 {age}일이 지났어요. 화면과 가격이 바뀌었을 수 있어요")
    if f.get("plans"):
        o += ["", "## 요금 (확인 기준일에 따라 달라질 수 있어요)", "", "| 플랜 | 월 요금 | 한국 원화(환산) |", "|---|---|---|"]
        for p in f["plans"]:
            usd = p.get("usd_month"); o.append(f"| {p['name']} | " + ("무료" if usd == 0 else f"${usd}" if usd is not None else "확인 필요") + " | " + ("0원" if usd == 0 else f"약 {krw(usd, f['usd_krw_rate']):,.0f}원" if usd is not None else "-") + " |")
        if any(p.get("usd_month") for p in f["plans"]): o.append(f"\n환율 {f['usd_krw_rate']:,}원/달러 ({f['rate_date']} 기준 입력값). 카드 수수료·부가세는 포함되지 않았어요.")
    o += ["", "## 따라 하기"]
    for i, s in enumerate(f["steps"], 1): o += [f"### {i}. {s['title']}", s["how"], f"[스크린샷 {i}: 직접 캡처해 넣어 주세요]", ""]
    o += ["## 좋았던 점"] + [f"- {x}" for x in f.get("pros", [])] + ["", "## 아쉬웠던 점"] + [f"- {x}" for x in f["cons"]]
    if f.get("korean_support"): o += ["", f"## 한국어 지원 상태", f["korean_support"]]
    o += ["", f"가입 링크: {f['affiliate_link']}", "", DISCLOSURE]
    return "\n".join(o) + "\n"


def check(text):
    out = []
    if DISCLOSURE[:12] not in text[:200]: out.append(("고지", "글 처음 200자 안에 제휴 고지가 없어요"))
    for w in BAD:
        if w in text: out.append(("과장", f"'{w}' 표현은 빼 주세요"))
    for m in re.finditer(r"\$\s?\d+", text):
        if "환율" not in text: out.append(("가격", "달러 가격이 있는데 환율·기준일 표기가 없어요")); break
    if text.count("스크린샷") < 2: out.append(("스크린샷", "직접 찍은 스크린샷 자리가 2개 미만이에요"))
    if not re.search(r"아쉬|단점|불편", text): out.append(("균형", "아쉬운 점이 없어요"))
    return out
