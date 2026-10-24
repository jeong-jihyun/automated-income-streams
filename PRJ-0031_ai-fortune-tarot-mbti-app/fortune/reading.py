"""상담 글 만들기. 기본은 규칙 기반 문장. llm(prompt)->str 함수를 꽂으면 AI 문장을 쓰되, 안전 필터를 반드시 거친다."""
from . import guard

SYSTEM = ("너는 재미와 성찰을 위한 상담 도우미다. 미래를 단정하지 말고, 건강·법률·투자·죽음·저주 이야기는 하지 말고, "
          "따뜻한 말로 선택은 본인에게 있음을 알려 줘라. 3문장 이내.")


def _template(question, cards, mbti, saju):
    parts = []
    for c in cards:
        parts.append(f"{c['position']} 자리의 '{c['card']}'{'(거꾸로)' if c['reversed'] else ''}는 {c['meaning']}의 기운을 말해 줍니다.")
    if mbti: parts.append(f"성향은 {mbti['type']} 쪽이라, 결정할 때 그 장점을 살려 보세요.")
    if saju:
        top = max(saju, key=saju.get); parts.append(f"오행에서는 '{top}' 기운이 두드러집니다.")
    parts.append("답은 점괘가 아니라 당신의 선택 안에 있습니다. 오늘 할 수 있는 작은 행동 하나를 정해 보세요.")
    return " ".join(parts)


def consult(question, cards=(), mbti=None, saju_elements=None, llm=None):
    kind, msg = guard.check_question(question)
    if kind != "ok": return {"kind": kind, "text": msg, "removed": 0, "source": "guard"}
    base = _template(question, cards, mbti, saju_elements)
    source, removed, text = "template", 0, base
    if llm:
        prompt = f"{SYSTEM}\n질문: {question}\n뽑은 카드: {[(c['position'], c['card'], c['reversed']) for c in cards]}\nMBTI: {mbti and mbti['type']}\n"
        try:
            raw = llm(prompt)
            text, removed = guard.filter_output(raw)
            source = "llm"
            if len(text) < 20: text, source = base, "template(llm 결과 부적합)"      # 거의 다 걸러졌으면 기본 문장으로 대체
        except Exception:
            text, source = base, "template(llm 오류)"
    return {"kind": "ok", "text": text + "\n" + guard.DISCLAIMER, "removed": removed, "source": source}
