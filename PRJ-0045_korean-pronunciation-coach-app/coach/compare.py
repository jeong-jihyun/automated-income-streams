"""목표 문장과 음성인식(STT) 결과의 글자(자모) 단위 비교. **소리 자체를 평가하지 않는다 — 인식기가 받아 적은 글만 비교한다.**"""
import re
from difflib import SequenceMatcher
from .g2p import pronounce
from .hangul import decompose, jamo

TIPS = {  # (목표 자모, 들린 자모) 또는 목표 자모 -> 안내
    ("ㅓ", "ㅗ"): "'ㅓ'는 입을 크게 벌려 '어', 'ㅗ'는 입술을 동그랗게 모아 '오'",
    ("ㅗ", "ㅓ"): "'ㅗ'는 입술을 동그랗게 모아 '오', 'ㅓ'는 '어'",
    ("ㅡ", "ㅜ"): "'ㅡ'는 입술을 펴고 '으', 'ㅜ'는 입술을 내밀어 '우'",
    ("ㅜ", "ㅡ"): "'ㅜ'는 입술을 내밀어 '우', 'ㅡ'는 입술을 펴고 '으'",
    ("ㅂ", "ㅍ"): "'ㅂ'(평음)은 숨을 세게 내지 않고, 'ㅍ'(격음)은 숨을 세게 내요",
    ("ㅍ", "ㅂ"): "'ㅍ'(격음)은 숨을 세게 내요", ("ㄱ", "ㅋ"): "'ㄱ'은 숨을 약하게, 'ㅋ'은 세게", ("ㅋ", "ㄱ"): "'ㅋ'은 숨을 세게 내요",
    ("ㄷ", "ㅌ"): "'ㄷ'은 숨을 약하게, 'ㅌ'은 세게", ("ㅌ", "ㄷ"): "'ㅌ'은 숨을 세게 내요", ("ㅈ", "ㅊ"): "'ㅈ'은 숨을 약하게, 'ㅊ'은 세게", ("ㅊ", "ㅈ"): "'ㅊ'은 숨을 세게 내요",
    ("ㄹ", "ㄴ"): "'ㄹ'은 혀끝을 윗잇몸에 살짝 튕겨요", ("ㄴ", "ㄹ"): "'ㄴ'은 혀끝을 윗잇몸에 붙인 채 코로 소리 내요",
}
EN_TIPS = {"ㅓ": "ㅓ ≈ 'uh' (mouth open)", "ㅗ": "ㅗ ≈ 'oh' (lips rounded)", "ㅡ": "ㅡ ≈ 'eu' (lips flat)", "ㅜ": "ㅜ ≈ 'oo' (lips rounded)"}
NOTE = "※ 이 결과는 음성인식기가 받아 적은 글과 목표 글을 비교한 것입니다. 실제 소리의 높낮이·길이·억양은 평가하지 못합니다."


def clean(s):
    return re.sub(r"[^가-힣]", "", s)


def compare(target, heard):
    t, h = clean(target), clean(heard)
    if not t: raise ValueError("목표 문장에 한글이 없습니다")
    if not h: return {"score": 0, "diffs": [], "empty": True, "target_sound": pronounce(t), "note": NOTE}
    tp = pronounce(t)
    tj, hj = jamo(tp), jamo(h)
    sm = SequenceMatcher(None, tj, hj, autojunk=False)
    diffs = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal": continue
        want, got = "".join(tj[a1:a2]), "".join(hj[b1:b2])
        tip = TIPS.get((want, got)) if len(want) == 1 and len(got) == 1 else None
        diffs.append({"want": want, "got": got, "kind": {"replace": "다르게 들림", "delete": "빠짐", "insert": "더 들어감"}[op], "tip": tip,
                      "tip_en": EN_TIPS.get(want) if tip else None})
    score = round(100 * sm.ratio())
    return {"score": score, "diffs": diffs, "empty": False, "target_sound": tp, "same_as_spelling": h == t, "note": NOTE}
