CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = [""] + list("ㄱㄲ") + ["ㄳ"] + list("ㄴ") + ["ㄵ", "ㄶ"] + list("ㄷㄹ") + ["ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ"] + list("ㅁㅂ") + ["ㅄ"] + list("ㅅㅆㅇㅈㅊㅋㅌㅍㅎ")
SPLIT = {"ㄳ": ("ㄱ", "ㅅ"), "ㄵ": ("ㄴ", "ㅈ"), "ㄶ": ("ㄴ", "ㅎ"), "ㄺ": ("ㄹ", "ㄱ"), "ㄻ": ("ㄹ", "ㅁ"), "ㄼ": ("ㄹ", "ㅂ"), "ㄽ": ("ㄹ", "ㅅ"), "ㄾ": ("ㄹ", "ㅌ"), "ㄿ": ("ㄹ", "ㅍ"), "ㅀ": ("ㄹ", "ㅎ"), "ㅄ": ("ㅂ", "ㅅ")}


def decompose(s):
    """한글 글자 -> [(초, 중, 종)] (한글이 아닌 글자는 건너뜀)"""
    out = []
    for ch in s:
        c = ord(ch) - 0xAC00
        if 0 <= c < 11172: out.append([CHO[c // 588], JUNG[(c % 588) // 28], JONG[c % 28]])
    return out


def compose(syl):
    return "".join(chr(0xAC00 + CHO.index(a) * 588 + JUNG.index(b) * 28 + JONG.index(c)) for a, b, c in syl)


def jamo(s):
    return [j for a, b, c in decompose(s) for j in (a, b, c) if j]
