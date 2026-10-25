"""계약서 글을 조항(제1조, 제2조 …)으로 나눈다. 조 번호가 없으면 번호 줄(1. 2. …)로 나눈다."""
import re


def split(text):
    t = text.replace("\r\n", "\n")
    pat = re.compile(r"^\s*(제\s*\d+\s*조[^\n]*)", re.M)
    ms = list(pat.finditer(t))
    if not ms:
        pat = re.compile(r"^\s*(\d+\.\s[^\n]*)", re.M); ms = list(pat.finditer(t))
    if not ms: return [{"no": "전체", "title": "", "text": t.strip()}] if t.strip() else []
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
        head = m.group(1).strip(); no = re.match(r"제\s*\d+\s*조|\d+\.", head).group(0).replace(" ", "")
        out.append({"no": no, "title": head, "text": t[m.start():end].strip()})
    return out
