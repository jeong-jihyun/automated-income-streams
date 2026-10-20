"""필수 글자 목록: KS X 1001 완성형 한글 2,350자 + 숫자·영문·기본 기호."""
import csv
import string


def ksx1001_hangul():
    """EUC-KR(KS X 1001) 한글 영역(0xB0A1~0xC8FE)을 풀어 2,350자를 만든다."""
    out = []
    for lead in range(0xB0, 0xC9):
        for trail in range(0xA1, 0xFF):
            try:
                ch = bytes([lead, trail]).decode("euc-kr")
            except UnicodeDecodeError:
                continue
            if "가" <= ch <= "힣":
                out.append(ch)
    return out


def basic_chars():
    punct = list(" .,:;!?'\"()[]{}-_/+=*&%#@~")
    return list(string.digits) + list(string.ascii_uppercase) + list(string.ascii_lowercase) + punct


def required_chars():
    return ksx1001_hangul() + basic_chars()


def write_csv(path, chars=None):
    chars = chars or required_chars()
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["character", "codepoint", "filename"])
        for ch in chars:
            w.writerow([ch, f"U+{ord(ch):04X}", f"U+{ord(ch):04X}.svg"])
    return len(chars)
