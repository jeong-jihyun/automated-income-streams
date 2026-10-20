"""표지 크기 계산과 가이드선이 있는 표지 PDF."""
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

PT = 72.0


def spine_width_in(pages, paper, specs):
    if paper not in specs["paper_thickness_in_per_page"]:
        raise ValueError(f"종이 종류 '{paper}' 없음. 선택: {', '.join(specs['paper_thickness_in_per_page'])}")
    return pages * specs["paper_thickness_in_per_page"][paper]


def cover_size_in(trim_in, pages, paper, specs):
    spine = spine_width_in(pages, paper, specs)
    b = specs["bleed_in"]
    return {"spine_in": round(spine, 4),
            "width_in": round(2 * trim_in[0] + spine + 2 * b, 4),
            "height_in": round(trim_in[1] + 2 * b, 4)}


def build_cover(out_pdf, title, trim_in, pages, paper, specs):
    s = cover_size_in(trim_in, pages, paper, specs)
    w, h = s["width_in"] * PT, s["height_in"] * PT
    b = specs["bleed_in"] * PT
    spine = s["spine_in"] * PT
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    c = canvas.Canvas(out_pdf, pagesize=(w, h))
    c.setStrokeColorRGB(0.8, 0.1, 0.1); c.setDash(4, 3)
    left = b + trim_in[0] * PT
    c.rect(left, b, spine, h - 2 * b)  # 책등
    c.rect(b, b, w - 2 * b, h - 2 * b)  # 재단선
    c.setFillColorRGB(0, 0, 0); c.setFont("HYSMyeongJo-Medium", 28)
    c.drawCentredString(left + spine + trim_in[0] * PT / 2, h * 0.6, title)
    c.setFont("Helvetica", 9)
    c.drawString(b + 10, b + 10, f"cover {s['width_in']}x{s['height_in']} in / spine {s['spine_in']} in / {pages} pages (guide lines: delete before upload)")
    c.save()
    return s
