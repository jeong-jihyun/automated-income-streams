from . import clauses, rules

ORDER = {rules.HIGH: 0, rules.MID: 1, rules.LOW: 2}
DISCLAIMER = "※ 법률 자문이 아닙니다. 규칙으로 문구를 찾아 쉬운 말로 알려 드리는 도구이며 놓치는 부분이 많습니다. 중요한 계약은 변호사 등 전문가에게 확인하세요."


def review(text):
    cs = clauses.split(text)
    if not cs: raise ValueError("계약서 내용이 비었습니다")
    found = sorted((f for c in cs for f in rules.review_clause(c)), key=lambda f: (ORDER[f["level"]], f["clause"]))
    return {"clauses": len(cs), "findings": found, "missing": rules.missing(text),
            "counts": {lv: sum(1 for f in found if f["level"] == lv) for lv in (rules.HIGH, rules.MID, rules.LOW)}}


def markdown(r):
    o = ["# 계약서 주의 조항 점검", "", f"조항 {r['clauses']}개 점검 — 높음 {r['counts']['높음']} · 중간 {r['counts']['중간']} · 참고 {r['counts']['참고']}", ""]
    for f in r["findings"]:
        o += [f"## [{f['level']}] {f['clause']} {f['title']}", f"- 문구: \"{f['snippet']}\"", f"- 쉬운 설명: {f['why']}", f"- 물어볼 것: {f['ask']}", ""]
    if not r["findings"]: o.append("규칙에 걸린 조항이 없습니다. 그래도 안전하다는 뜻은 아닙니다.\n")
    if r["missing"]: o.append("빠진 것처럼 보이는 내용: " + ", ".join(r["missing"]) + "\n")
    return "\n".join(o) + DISCLAIMER + "\n"
