"""간이 발음 변환(표기 → 소리). 연음·종성 대표음·비음화·격음화·경음화 일부·ㄴㄹ 첨가 없음. **전체 한국어 발음 규칙이 아니다.**"""
from .hangul import decompose, compose, SPLIT

REP = {"ㄲ": "ㄱ", "ㅋ": "ㄱ", "ㄳ": "ㄱ", "ㄺ": "ㄱ", "ㅅ": "ㄷ", "ㅆ": "ㄷ", "ㅈ": "ㄷ", "ㅊ": "ㄷ", "ㅌ": "ㄷ", "ㅎ": "ㄷ", "ㅍ": "ㅂ", "ㅄ": "ㅂ", "ㄿ": "ㅂ", "ㄼ": "ㄹ", "ㄽ": "ㄹ", "ㄾ": "ㄹ", "ㅀ": "ㄹ", "ㄵ": "ㄴ", "ㄶ": "ㄴ", "ㄻ": "ㅁ"}
NASAL = {"ㄱ": "ㅇ", "ㄷ": "ㄴ", "ㅂ": "ㅁ"}
ASP = {"ㄱ": "ㅋ", "ㄷ": "ㅌ", "ㅂ": "ㅍ", "ㅈ": "ㅊ"}


def pronounce(text):
    syl = decompose(text)
    for i in range(len(syl) - 1):
        a, b = syl[i], syl[i + 1]
        if not a[2]: continue
        # ㅎ 받침 + 평음 -> 격음 (좋다 -> 조타)
        if a[2] == "ㅎ" and b[0] in ASP: b[0] = ASP[b[0]]; a[2] = ""; continue
        if a[2] in ("ㄶ", "ㅀ") and b[0] in ASP: b[0] = ASP[b[0]]; a[2] = SPLIT[a[2]][0]; continue
        # 평음 받침 + ㅎ -> 격음 (축하 -> 추카)
        if b[0] == "ㅎ" and REP.get(a[2], a[2]) in ASP and a[2] not in ("ㅎ",):
            b[0] = ASP[REP.get(a[2], a[2])]; a[2] = ""; continue
        # 연음: 받침 + 모음(ㅇ) -> 받침이 다음 글자 첫소리로
        if b[0] == "ㅇ":
            if a[2] == "ㅇ": continue
            if a[2] in SPLIT: keep, mv = SPLIT[a[2]]; a[2] = keep; b[0] = mv
            elif a[2] == "ㅎ": a[2] = ""
            else: b[0] = a[2]; a[2] = ""
            continue
        rep = REP.get(a[2], a[2]); a[2] = rep
        # 비음화: ㄱㄷㅂ + ㄴㅁ -> ㅇㄴㅁ ; ㅁㅇ + ㄹ -> ㄴ
        if rep in NASAL and b[0] in ("ㄴ", "ㅁ"): a[2] = NASAL[rep]
        elif rep in ("ㅁ", "ㅇ") and b[0] == "ㄹ": b[0] = "ㄴ"
        elif rep in NASAL and b[0] == "ㄹ": a[2] = NASAL[rep]; b[0] = "ㄴ"
    if syl and syl[-1][2]: syl[-1][2] = REP.get(syl[-1][2], syl[-1][2])
    return compose([s for s in syl])
