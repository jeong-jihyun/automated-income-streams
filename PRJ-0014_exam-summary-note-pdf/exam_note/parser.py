"""요약 원고(마크다운 일부)를 읽어 블록으로 바꾸고 형식을 점검한다.
지원 문법: # 제목(1개) / ## 장 / ### 절 / 문단 / - 목록 / 표 / > 용어: 설명 / Q: 문제 + A: 정답"""
import re

BANNED = ["합격 보장", "합격보장", "100% 합격", "100%합격", "무조건 합격", "합격 확정", "불합격 환불 없이 합격"]
TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")


class ManuscriptError(ValueError):
    pass


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(text):
    blocks, problems = [], []
    lines = text.splitlines()
    i, para = 0, []

    def flush():
        if para:
            blocks.append({"type": "p", "text": " ".join(para)}); para.clear()

    while i < len(lines):
        raw = lines[i]; line = raw.strip(); n = i + 1
        if not line:
            flush(); i += 1; continue
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            flush(); blocks.append({"type": f"h{len(m.group(1))}", "text": m.group(2).strip(), "line": n}); i += 1; continue
        if line.startswith("- "):
            flush(); items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:].strip()); i += 1
            blocks.append({"type": "ul", "items": items}); continue
        if line.startswith(">"):
            flush(); terms = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                body = lines[i].strip()[1:].strip()
                if ":" not in body or not body.split(":", 1)[0].strip() or not body.split(":", 1)[1].strip():
                    problems.append((i + 1, "용어 박스는 '> 용어: 설명' 형식이어야 합니다"))
                else:
                    k, v = body.split(":", 1); terms.append((k.strip(), v.strip()))
                i += 1
            if terms:
                blocks.append({"type": "terms", "items": terms})
            continue
        if line.startswith("|"):
            flush(); rows = []; start = i + 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            if len(rows) < 2 or not TABLE_SEP.match(rows[1]):
                problems.append((start, "표는 둘째 줄에 |---|---| 구분선이 필요합니다"))
                continue
            header = split_row(rows[0]); body = [split_row(r) for r in rows[2:]]
            if any(len(r) != len(header) for r in body):
                problems.append((start, "표의 줄마다 칸 수가 같아야 합니다"))
                continue
            blocks.append({"type": "table", "header": header, "rows": body}); continue
        if re.match(r"^Q:\s*", line):
            flush()
            q = line[2:].strip(); ans = None
            if i + 1 < len(lines) and re.match(r"^A:\s*", lines[i + 1].strip()):
                ans = lines[i + 1].strip()[2:].strip(); i += 1
            else:
                problems.append((n, "Q: 문제 다음 줄에 A: 정답이 필요합니다"))
            if not q:
                problems.append((n, "Q: 뒤에 문제 내용이 비어 있습니다"))
            blocks.append({"type": "qa", "q": q, "a": ans or ""}); i += 1; continue
        if re.match(r"^A:\s*", line):
            problems.append((n, "정답(A:)이 문제(Q:) 없이 나왔습니다"))
            i += 1; continue
        para.append(line); i += 1
    flush()
    h1 = [b for b in blocks if b["type"] == "h1"]
    if len(h1) != 1:
        problems.append((0, f"제목(# )은 정확히 1개여야 합니다 (현재 {len(h1)}개)"))
    if not any(b["type"] == "h2" for b in blocks):
        problems.append((0, "장(## )이 하나도 없습니다"))
    for b in blocks:
        if b["type"] in ("h2", "h3") and not b["text"]:
            problems.append((b.get("line", 0), "제목 글자가 비어 있습니다"))
    return blocks, sorted(problems)


def banned_phrases(text):
    return [b for b in BANNED if b in text.replace("\u00a0", " ")]


def all_text(blocks):
    out = []
    for b in blocks:
        if b["type"] in ("h1", "h2", "h3", "p"): out.append(b["text"])
        elif b["type"] == "ul": out += b["items"]
        elif b["type"] == "terms": out += [f"{k} {v}" for k, v in b["items"]]
        elif b["type"] == "table": out += b["header"] + [c for r in b["rows"] for c in r]
        elif b["type"] == "qa": out += [b["q"], b["a"]]
    return "\n".join(out)
