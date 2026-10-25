"""주의할 조항을 찾는 규칙. **기준 수치와 문구는 제가 정한 예시이며 변호사 검토를 받은 것이 아닙니다.**"""
import re

HIGH, MID, LOW = "높음", "중간", "참고"


def _pct(t):
    return [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|퍼센트)", t)]


def _days(t, near):
    """'지급 ... 90일' 과 '90일 이내에 ... 지급' 두 순서 모두 찾는다."""
    a = [int(m.group(1)) for m in re.finditer(near + r".{0,30}?(\d+)\s*일", t)]
    b = [int(m.group(1)) for m in re.finditer(r"(\d+)\s*일\s*(이내|내|후|뒤).{0,20}?" + near, t)]
    return a + b


RULES = [  # (id, 제목, 수준, 찾는 방법(함수), 쉬운 설명, 확인할 질문)
    ("auto_renew", "자동 갱신", MID, lambda t: re.search(r"자동(으로)?\s*(갱신|연장)", t), "해지하지 않으면 계약이 저절로 이어져요.", "해지 통보는 언제까지 해야 하나요? 갱신 때 가격이 오르나요?"),
    ("one_sided", "일방적 해지·변경", HIGH, lambda t: re.search(r"(일방적으로|임의로|언제든(지)?|사전 통지 없이|통보 없이).{0,25}(해지|변경|종료|중단)", t) or re.search(r"(해지|변경|종료|중단).{0,15}(일방적|임의)", t), "한쪽이 마음대로 계약을 끝내거나 바꿀 수 있어 보여요.", "상대방도 같은 권리가 있나요? 사전 통지 기간이 있나요?"),
    ("penalty", "위약금·손해배상 예정", MID, lambda t: re.search(r"위약금|손해배상(액)?의 예정|지체상금", t), "계약을 어기면 정해 둔 돈을 물어야 해요.", "금액·비율이 내 책임에 비해 적당한가요? 상한이 있나요?"),
    ("penalty_high", "높은 비율의 위약금", HIGH, lambda t: re.search(r"위약금|손해배상|지체상금", t) and any(p >= 30 for p in _pct(t)), "위약금 비율이 높아 보여요(30% 이상, 예시 기준).", "이 비율의 근거는 무엇인가요? 낮출 수 있나요?"),
    ("unlimited", "무제한 책임", HIGH, lambda t: re.search(r"(일체의|모든)\s*(손해|책임|비용)|한도\s*없이|전액\s*배상", t), "생긴 손해를 모두 책임질 수 있어 보여요.", "책임 한도(예: 계약 금액까지)를 정할 수 있나요?"),
    ("ip", "저작권·지식재산권 귀속", MID, lambda t: re.search(r"(저작권|지식재산권|지적재산권|특허).{0,30}(귀속|양도|이전)|(귀속|양도).{0,20}(저작권|지식재산권)", t), "결과물의 권리가 누구에게 가는지 정해져 있어요.", "내가 만든 결과물의 권리가 모두 넘어가나요? 내가 계속 써도 되나요?"),
    ("confid", "기간 없는 비밀유지", MID, lambda t: re.search(r"(영구(히)?|기간의 제한 없이|무기한).{0,20}비밀|비밀.{0,30}(영구|무기한|기간의 제한 없이)", t), "비밀을 지켜야 하는 기간이 끝없이 이어져요.", "비밀유지 기간을 정할 수 있나요?"),
    ("noncompete", "경업·겸업 금지", MID, lambda t: re.search(r"경업|겸업\s*금지|동종\s*업종.{0,20}(금지|종사)", t), "계약 중이나 뒤에 비슷한 일을 못 할 수 있어요.", "금지 기간·범위가 너무 넓지 않나요?"),
    ("late_pay", "늦은 대금 지급", MID, lambda t: re.search(r"지급|대금|결제", t) and any(d >= 60 for d in _days(t, r"(지급|결제|지불)")), "돈을 받는 날이 많이 늦을 수 있어요(60일 이상, 예시 기준).", "지급 기한을 줄일 수 있나요? 늦으면 이자가 있나요?"),
    ("disclaim", "책임 면제", MID, lambda t: re.search(r"책임을\s*지지\s*(아니|않)|면책|어떠한\s*책임도", t), "한쪽이 책임을 지지 않는다고 적혀 있어요.", "어떤 경우에도 책임이 없다는 뜻인가요? 고의·중과실은 제외되나요?"),
    ("vague", "모호한 판단 문구", MID, lambda t: re.search(r"(갑|을|회사|발주자|운영자)(이|가|은|는)\s*(필요하다고|적절하다고)\s*(인정|판단)|기타\s*필요한\s*경우", t), "한쪽의 판단에 따라 달라질 수 있는 표현이에요.", "기준을 구체적으로 적을 수 있나요?"),
    ("venue", "관할 법원", LOW, lambda t: re.search(r"관할\s*(법원|으로)", t), "다툼이 생기면 재판할 법원이 정해져 있어요.", "내가 가기 불편한 먼 곳인가요?"),
]
EXPECTED = {"계약 기간": r"계약\s*기간|유효\s*기간|존속\s*기간", "대금(금액)": r"대금|금액|보수|요금|임대료", "해지": r"해지|해제", "분쟁 해결": r"분쟁|관할|중재|준거법"}


def review_clause(c):
    out = []
    for rid, title, level, fn, why, ask in RULES:
        m = fn(c["text"])
        if m:
            snippet = m.group(0) if hasattr(m, "group") else ""
            out.append({"clause": c["no"], "title": title, "level": level, "why": why, "ask": ask, "snippet": snippet.strip()[:60]})
    return out


def missing(text):
    return [k for k, p in EXPECTED.items() if not re.search(p, text)]
