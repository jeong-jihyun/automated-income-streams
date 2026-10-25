"""등기부 항목을 쉬운 말로 풀이하고 주의 사항을 표시한다. **기준 수치와 목록은 제가 정한 예시이며 전문가 검토를 받지 않았습니다.**"""
import re
from .registry import won

GAP_RISKS = [  # (찾는 말, 수준, 쉬운 설명)
    ("경매개시결정", "매우 높음", "집이 경매에 넘어가는 절차가 시작됐어요."), ("가압류", "높음", "빚 문제로 집을 임시로 묶어 둔 상태예요(나중에 팔릴 수 있어요)."), ("압류", "높음", "나라나 기관이 이 집을 못 팔게 묶어 둔 상태예요."),
    ("가처분", "높음", "집을 팔거나 넘기는 것을 법원이 임시로 막아 둔 상태예요."), ("가등기", "높음", "나중에 집 주인이 바뀔 수 있는 예약 등기가 있어요."), ("신탁", "높음", "집이 신탁회사 명의라 실제 주인과 계약 상대가 다를 수 있어요."),
    ("예고등기", "높음", "집의 권리를 다투는 소송이 예고돼 있어요."),
]
EUL_RISKS = [("전세권", "중간", "전세권이 이미 잡혀 있어요. 내 보증금이 뒤로 밀릴 수 있어요."), ("임차권등기", "높음", "앞서 살던 세입자가 보증금을 못 받아 등기를 해 둔 집이에요."), ("지상권", "중간", "다른 사람이 이 땅을 쓸 수 있는 권리가 잡혀 있어요.")]


def level_rank(l):
    return {"매우 높음": 0, "높음": 1, "중간": 2, "참고": 3}[l]


def analyze(reg, price=None, deposit=0, landlord=None, ratio_limit=0.70):
    findings, mortgage = [], 0
    owner = None
    for e in reg["gap"]:
        if "소유권이전" in e["text"] or "소유권보존" in e["text"]:
            m = re.search(r"소유자\s*([가-힣A-Za-z]+)", e["text"]); owner = m.group(1) if m else owner
        for key, lv, why in GAP_RISKS:
            if key in e["text"]:
                findings.append({"where": f"갑구 {e['no']}번", "kind": key, "level": lv, "why": why}); break
    for e in reg["eul"]:
        if "근저당" in e["text"]:
            amt = won(e["text"][e["text"].find("채권최고액"):]) if "채권최고액" in e["text"] else None
            if amt: mortgage += amt
            findings.append({"where": f"을구 {e['no']}번", "kind": "근저당권", "level": "참고", "why": f"집을 담보로 빚이 잡혀 있어요(채권최고액 {amt:,}원)." if amt else "근저당이 있으나 금액을 읽지 못했어요."})
        else:
            for key, lv, why in EUL_RISKS:
                if key in e["text"]: findings.append({"where": f"을구 {e['no']}번", "kind": key, "level": lv, "why": why}); break
    out = {"owner": owner, "mortgage": mortgage, "findings": [], "ratio": None, "ratio_warn": False, "owner_mismatch": False}
    if price:
        out["ratio"] = round((mortgage + deposit) / price, 3)
        if out["ratio"] > ratio_limit:
            out["ratio_warn"] = True
            findings.append({"where": "전체", "kind": "빚+보증금 비율", "level": "높음", "why": f"근저당({mortgage:,}원)과 내 보증금({deposit:,}원)을 더하면 집값의 {out['ratio']*100:.0f}%예요. {int(ratio_limit*100)}%가 넘으면 경매 시 보증금을 못 돌려받을 위험이 커져요(예시 기준)."})
    if landlord and owner and landlord.replace(" ", "") != owner:
        out["owner_mismatch"] = True
        findings.append({"where": "갑구", "kind": "소유자 불일치", "level": "매우 높음", "why": f"등기부 소유자({owner})와 계약서의 임대인({landlord})이 달라요. 대리 계약이면 위임장과 신분을 꼭 확인해야 해요."})
    out["findings"] = sorted(findings, key=lambda f: level_rank(f["level"]))
    return out


SPECIAL = {"보증금 반환": r"보증금.{0,15}(반환|돌려)", "전입신고·확정일자": r"전입신고|확정일자|대항력", "근저당 말소·유지 조건": r"근저당.{0,20}(말소|유지|설정\s*금지)|담보\s*설정", "잔금일 권리 유지": r"잔금.{0,20}(권리|등기).{0,15}(변동|유지)|현\s*상태\s*유지"}


def special_terms(text):
    return [k for k, p in SPECIAL.items() if not re.search(p, text)]
