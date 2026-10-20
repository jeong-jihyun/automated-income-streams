"""교재 PDF: 상황별로 문장·뜻·발음 표."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


def build_pdf(out_pdf, title, chapter_rows, font):
    pdfmetrics.registerFont(UnicodeCIDFont(font))
    W, H = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)
    pages = 1

    def new_page():
        nonlocal pages
        c.showPage(); pages += 1; c.setFont(font, 11)

    c.setFont(font, 24); c.drawString(50, H - 120, title)
    c.setFont(font, 11); c.drawString(50, H - 150, "직접 쓴 문장으로 만든 교재입니다.")
    c.showPage()
    pages = 2  # 표지 + 본문 첫 쪽
    c.setFont(font, 11)
    y = H - 60
    for name, rows in chapter_rows:
        if y < 120:
            new_page(); y = H - 60
        c.setFont(font, 16); c.drawString(50, y, name); y -= 28; c.setFont(font, 11)
        for r in rows:
            if y < 90:
                new_page(); y = H - 60
            c.drawString(50, y, f"{r['no']}. {r['text']}"); y -= 16
            c.drawString(70, y, r["meaning"]); y -= 16
            if r["pronunciation"]:
                c.drawString(70, y, f"[{r['pronunciation']}]"); y -= 16
            y -= 8
        y -= 12
    c.save()
    return pages
