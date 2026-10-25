from .cut import ts

DISCLAIMER = "※ 자막 글만 보고 고른 구간입니다. 영상 화면·소리는 분석하지 않았고 자막이 틀리면 결과도 틀립니다. 저작권이 있는 영상은 권리자 허락 없이 공유하지 마세요."


def markdown(title, segs, hl, summ):
    o = [f"# {title} 요약", "", "## 한눈에 보기"] + [f"- {s}" for s in summ] + ["", "## 목차"]
    o += [f"- {ts(s['start'])[:8]} {s['title']}" for s in segs]
    o += ["", "## 하이라이트 구간"] + [f"{i}. {ts(h['start'])[:8]} ~ {ts(h['end'])[:8]} — {h['title']}" for i, h in enumerate(hl, 1)]
    return "\n".join(o) + "\n\n" + DISCLAIMER + "\n"
