"""안전 장치: 위기 표현은 상담 안내로 돌리고, 의료·법률·투자 결정은 풀이로 답하지 않으며, 단정·공포 표현은 걸러낸다."""
import re

CRISIS = re.compile(r"자살|죽고\s*싶|스스로.*목숨|자해|살기\s*싫")
DECISION = re.compile(r"(병|암|수술|약).*(낫|걸렸|치료|먹어)|소송|이혼\s*소송|(주식|코인|비트코인|투자|대출).*(사|팔|할까|해도)|임신|유산")
ABSOLUTE = re.compile(r"반드시|100\s*%|틀림없이|절대로?|무조건|죽는다|사망|암에|불치|저주|액운|재앙")
CRISIS_MSG = "많이 힘드신 것 같아요. 점괘보다 지금은 사람의 도움이 더 중요합니다. 가까운 사람이나 자살예방상담전화 109(24시간)에 바로 이야기해 보세요. 위급하면 112·119에 연락하세요."
DECISION_MSG = "건강·법률·돈이 걸린 결정은 점으로 정할 수 없어요. 의사·변호사·금융 전문가와 상의하세요. 마음의 흐름을 가볍게 돌아보는 질문이라면 다시 물어봐 주세요."
DISCLAIMER = "※ 재미와 자기 성찰을 위한 풀이이며 미래를 단정하지 않습니다."


def check_question(q):
    if CRISIS.search(q): return "crisis", CRISIS_MSG
    if DECISION.search(q): return "decision", DECISION_MSG
    return "ok", ""


def filter_output(text):
    """단정·공포 문장은 통째로 뺀다. 빠진 개수를 함께 돌려준다."""
    parts = [s for s in re.split(r"(?<=[.!?。])\s+|\n", text) if s.strip()]
    keep = [s for s in parts if not ABSOLUTE.search(s)]
    return " ".join(keep), len(parts) - len(keep)
