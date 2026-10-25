"""등기부등본 텍스트(표제부·갑구·을구)를 읽어 항목으로 나눈다. 말소된 항목은 현재 권리에서 뺀다. 실제 등기소에서 가져오지 않는다(사용자가 준 글만 처리)."""
import re


class RegError(ValueError):
    pass


def won(s):
    m = re.search(r"금?\s*([\d,]+)\s*원", s)
    return int(m.group(1).replace(",", "")) if m else None


def sections(text):
    idx = {k: text.find(k) for k in ("【갑구】", "【을구】")}
    if idx["【갑구】"] < 0 and idx["【을구】"] < 0: raise RegError("등기부 글에서 【갑구】【을구】를 찾지 못했습니다")
    order = sorted((v, k) for k, v in idx.items() if v >= 0)
    out = {"갑구": "", "을구": ""}
    for i, (pos, k) in enumerate(order):
        end = order[i + 1][0] if i + 1 < len(order) else len(text)
        out[k.strip("【】")] = text[pos + len(k):end]
    return out


def entries(sec):
    parts = re.split(r"(?m)^\s*(\d+(?:-\d+)?)\s+(?=\S)", sec)
    out = []
    for i in range(1, len(parts) - 1, 2):
        body = parts[i + 1].strip()
        if body.startswith(("순위번호", "등기목적")) or not body: continue
        out.append({"no": parts[i], "text": " ".join(body.split())})
    return out


def active(es):
    """'N번…말소' 항목이 가리키는 N번 항목은 빼고, 말소 항목 자체도 뺀다."""
    gone = set()
    for e in es:
        m = re.match(r"(\d+(?:-\d+)?)번.*말소", e["text"])
        if m: gone.add(m.group(1)); gone.add(e["no"])
    return [e for e in es if e["no"] not in gone]


def parse(text):
    s = sections(text)
    return {"gap": active(entries(s["갑구"])), "eul": active(entries(s["을구"]))}
