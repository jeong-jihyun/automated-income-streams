"""문장표 CSV 읽기와 점검."""
import csv
import os

REQUIRED = ["no", "situation", "text", "meaning"]


def read_sheet(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"문장표 CSV가 없습니다: {path}")
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames or []
        rows = [{k: (v or "").strip() for k, v in r.items() if k} for r in rd]
    missing = [c for c in REQUIRED if c not in cols]
    if missing:
        raise ValueError(f"문장표에 필요한 열이 없습니다: {', '.join(missing)}")
    if not rows:
        raise ValueError("문장표에 문장이 한 줄도 없습니다.")
    for r in rows:
        r.setdefault("pronunciation", "")
    return rows


def check_rows(rows, max_len):
    problems, seen_text, seen_no = [], {}, {}
    for i, r in enumerate(rows, start=2):
        for c in REQUIRED:
            if not r[c]:
                problems.append((i, f"'{c}' 칸이 비어 있습니다"))
        if r["no"] and not r["no"].isdigit():
            problems.append((i, "번호(no)는 숫자여야 합니다"))
        elif r["no"] in seen_no:
            problems.append((i, f"번호 {r['no']} 가 {seen_no[r['no']]}행과 겹칩니다"))
        elif r["no"]:
            seen_no[r["no"]] = i
        t = r["text"].lower()
        if t:
            if t in seen_text:
                problems.append((i, f"같은 문장이 {seen_text[t]}행에도 있습니다"))
            else:
                seen_text[t] = i
        if len(r["text"]) > max_len:
            problems.append((i, f"문장이 너무 깁니다 ({len(r['text'])}자 > {max_len}자)"))
    return problems


def chapters(rows):
    """상황(situation)별로 처음 나온 순서대로 묶는다."""
    out = {}
    for r in rows:
        out.setdefault(r["situation"], []).append(r)
    return out
