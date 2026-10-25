DISCLAIMER = "※ 법률·부동산 전문가의 자문이 아닙니다. 사용자가 준 글만 규칙으로 읽은 것이며 놓치는 내용이 많습니다. 계약 전에 최신 등기부를 직접 발급하고 공인중개사·변호사 등 전문가와 확인하세요."


def markdown(a, missing_terms=None):
    o = ["# 등기부·계약 쉬운 풀이", ""]
    if a["owner"]: o.append(f"- 현재 소유자(글에서 읽은 값): {a['owner']}")
    o.append(f"- 현재 남아 있는 근저당 채권최고액 합계: {a['mortgage']:,}원")
    if a["ratio"] is not None: o.append(f"- (근저당 + 내 보증금) ÷ 집값 = {a['ratio']*100:.0f}%")
    o += ["", "## 주의할 점"]
    o += [f"- **[{f['level']}] {f['kind']}** ({f['where']}): {f['why']}" for f in a["findings"]] or ["- 규칙에 걸린 항목이 없습니다. 그래도 안전하다는 뜻은 아닙니다."]
    if missing_terms: o += ["", "## 계약서 특약에서 빠진 것 같은 내용(확인해 보세요)"] + [f"- {m}" for m in missing_terms]
    return "\n".join(o) + "\n\n" + DISCLAIMER + "\n"
