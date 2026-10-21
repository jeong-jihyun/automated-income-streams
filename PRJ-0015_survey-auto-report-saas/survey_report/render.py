"""HTML 보고서(SVG 막대그래프 포함)와 간단한 PDF."""
import html
from xml.sax.saxutils import escape


def bar_svg(pairs, width=420, bar_h=22):
    if not pairs:
        return ""
    mx = max(n for _, n in pairs) or 1
    h = bar_h * len(pairs) + 10
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" role="img">']
    for i, (label, n) in enumerate(pairs):
        w = int((width - 160) * n / mx)
        y = 5 + i * bar_h
        out.append(f'<text x="0" y="{y + 15}" font-size="12">{escape(str(label))}</text>')
        out.append(f'<rect x="110" y="{y + 2}" width="{w}" height="{bar_h - 6}" fill="#3B6FB6"/>')
        out.append(f'<text x="{114 + w}" y="{y + 15}" font-size="12">{n}</text>')
    out.append("</svg>")
    return "".join(out)


def html_report(res, title):
    parts = [f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title>",
             "<style>body{font-family:sans-serif;max-width:760px;margin:2em auto;line-height:1.6}h2{margin-top:1.6em}</style>",
             f"<h1>{html.escape(title)}</h1><p>응답 {res['n']}건</p>"]
    if res["dropped"]:
        parts.append(f"<p><b>개인정보로 보이는 열을 보고서에서 뺐습니다:</b> {html.escape(', '.join(res['dropped']))}</p>")
    elif res["pii"]:
        parts.append(f"<p><b>주의: 개인정보로 보이는 열이 포함됩니다:</b> {html.escape(', '.join(res['pii']))}</p>")
    for c in res["columns"]:
        parts.append(f"<h2>{html.escape(c['name'])}</h2><p>응답 {c['answered']} / 빈칸 {c['missing']}</p>")
        if c["type"] == "number":
            parts.append(f"<p>평균 {c['mean']} · 중앙값 {c['median']} · 최소 {c['min']} · 최대 {c['max']}</p>")
            parts.append(bar_svg([(k, v) for k, v in c["dist"]]))
        elif c["type"] == "choice":
            parts.append(bar_svg(c["dist"]))
        elif c["type"] == "text":
            kw = ", ".join(f"{w}({n})" for w, n in c["keywords"]) or "없음"
            parts.append(f"<p>자주 나온 말: {html.escape(kw)}</p>")
        else:
            parts.append("<p>응답이 없습니다.</p>")
    parts.append("<hr><p><small>이 요약은 단순 집계입니다. 해석은 사람이 확인하세요.</small></p>")
    return "\n".join(parts)


def pdf_report(res, title, out_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    st = ParagraphStyle("b", fontName="HYSMyeongJo-Medium", fontSize=11, leading=17)
    h = ParagraphStyle("h", parent=st, fontSize=14, leading=20, spaceBefore=10)
    story = [Paragraph(escape(title), ParagraphStyle("t", parent=h, fontSize=20)), Paragraph(f"응답 {res['n']}건", st)]
    if res["dropped"]:
        story.append(Paragraph("개인정보 열 제외: " + escape(", ".join(res["dropped"])), st))
    for c in res["columns"]:
        story += [Paragraph(escape(c["name"]), h)]
        if c["type"] == "number":
            story.append(Paragraph(f"평균 {c['mean']} / 중앙값 {c['median']} / 최소 {c['min']} / 최대 {c['max']}", st))
        elif c["type"] == "choice":
            story.append(Paragraph(escape(", ".join(f"{k} {v}" for k, v in c["dist"])), st))
        elif c["type"] == "text":
            story.append(Paragraph(escape(", ".join(f"{w}({n})" for w, n in c["keywords"]) or "없음"), st))
    SimpleDocTemplate(out_path, pagesize=A4, title=title).build(story)
