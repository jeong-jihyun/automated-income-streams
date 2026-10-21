"""PDF 만들기: 표지, 목차(쪽번호), 본문, 핵심 용어 박스, 암기표, 확인 문제·정답. 인쇄용/태블릿용."""
import os
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents
from xml.sax.saxutils import escape

LAYOUTS = {
    "print": {"pagesize": A4, "margin": (22 * mm, 20 * mm), "body": 10.5, "label": "인쇄용 A4"},
    "tablet": {"pagesize": (160 * mm, 213 * mm), "margin": (12 * mm, 12 * mm), "body": 11.5, "label": "태블릿용"},
}


def register_font(font_path=None):
    """글꼴 파일이 있으면 PDF 안에 넣고(TTF), 없으면 기본 한글 글꼴(CID, 파일 미포함)을 쓴다. (글꼴 이름, 포함 여부) 반환."""
    if font_path:
        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"글꼴 파일이 없습니다: {font_path}")
        pdfmetrics.registerFont(TTFont("NoteFont", font_path))
        return "NoteFont", True
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    return "HYSMyeongJo-Medium", False


class Doc(BaseDocTemplate):
    def __init__(self, path, layout, title, **kw):
        L = LAYOUTS[layout]
        super().__init__(path, pagesize=L["pagesize"], leftMargin=L["margin"][0], rightMargin=L["margin"][0],
                         topMargin=L["margin"][1], bottomMargin=L["margin"][1], title=title, pageCompression=0, **kw)
        self.headings = []  # (레벨, 글자, 쪽)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=self._footer)])

    def _footer(self, canv, doc):
        canv.saveState(); canv.setFont(self._font, 8)
        canv.drawCentredString(doc.pagesize[0] / 2, 10 * mm, str(doc.page)); canv.restoreState()

    def beforeDocument(self):
        self.headings = []  # 패스마다 초기화 (키가 매번 같아야 목차가 수렴)

    def afterFlowable(self, fl):
        lvl = getattr(fl, "_toc_level", None)
        if lvl is not None:
            text = fl.getPlainText()
            key = f"h{len(self.headings)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=lvl, closed=False)
            self.notify("TOCEntry", (lvl, text, self.page, key))
            self.headings.append((lvl, text, self.page))


def build_pdf(blocks, out_pdf, layout="print", font_path=None, with_quiz=True):
    """PDF를 만들고 {'pages','headings','embedded'} 를 돌려준다."""
    if layout not in LAYOUTS:
        raise ValueError(f"레이아웃은 {', '.join(LAYOUTS)} 중 하나")
    font, embedded = register_font(font_path)
    L = LAYOUTS[layout]; b = L["body"]
    ss = {
        "title": ParagraphStyle("title", fontName=font, fontSize=26, leading=34, spaceAfter=18),
        "h2": ParagraphStyle("h2", fontName=font, fontSize=b + 6, leading=b + 11, spaceBefore=16, spaceAfter=8,
                              textColor=colors.HexColor("#1F3864")),
        "h3": ParagraphStyle("h3", fontName=font, fontSize=b + 2, leading=b + 7, spaceBefore=10, spaceAfter=4),
        "p": ParagraphStyle("p", fontName=font, fontSize=b, leading=b * 1.6, spaceAfter=6, alignment=TA_LEFT),
        "li": ParagraphStyle("li", fontName=font, fontSize=b, leading=b * 1.5, leftIndent=12, bulletIndent=2),
        "cell": ParagraphStyle("cell", fontName=font, fontSize=b - 1, leading=(b - 1) * 1.4),
        "toc": ParagraphStyle("toc", fontName=font, fontSize=b, leading=b * 1.6),
        "toc1": ParagraphStyle("toc1", fontName=font, fontSize=b, leading=b * 1.6, leftIndent=0),
        "toc2": ParagraphStyle("toc2", fontName=font, fontSize=b - 1, leading=b * 1.5, leftIndent=14),
    }
    doc = Doc(out_pdf, layout, next((x["text"] for x in blocks if x["type"] == "h1"), "요약노트"))
    doc._font = font
    toc = TableOfContents()
    toc.levelStyles = [ss["toc1"], ss["toc2"]]
    story = []

    def heading(text, style, level):
        p = Paragraph(escape(text), ss[style]); p._toc_level = level; return p

    title = next((x["text"] for x in blocks if x["type"] == "h1"), "요약노트")
    story += [Spacer(1, 60 * mm), Paragraph(escape(title), ss["title"]), Paragraph(escape(L["label"]), ss["p"]),
              PageBreak(), Paragraph("목차", ss["h2"]), toc, PageBreak()]
    qas = []
    for blk in blocks:
        t = blk["type"]
        if t == "h1":
            continue
        if t == "h2":
            if story and not isinstance(story[-1], PageBreak) and any(isinstance(s, Paragraph) and getattr(s, "_toc_level", None) == 0 for s in story):
                story.append(PageBreak())
            story.append(heading(blk["text"], "h2", 0))
        elif t == "h3":
            story.append(heading(blk["text"], "h3", 1))
        elif t == "p":
            story.append(Paragraph(escape(blk["text"]), ss["p"]))
        elif t == "ul":
            for it in blk["items"]:
                story.append(Paragraph(escape(it), ss["li"], bulletText="•"))
            story.append(Spacer(1, 4))
        elif t == "terms":
            data = [[Paragraph(f"<b>{escape(k)}</b>", ss["cell"]), Paragraph(escape(v), ss["cell"])] for k, v in blk["items"]]
            tb = Table(data, colWidths=[doc.width * 0.28, doc.width * 0.72])
            tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF3FA")),
                                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#1F3864")),
                                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8C6E0")),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story += [KeepTogether([tb]), Spacer(1, 8)]
        elif t == "table":
            data = [[Paragraph(f"<b>{escape(c)}</b>", ss["cell"]) for c in blk["header"]]] + \
                   [[Paragraph(escape(c), ss["cell"]) for c in r] for r in blk["rows"]]
            tb = Table(data, repeatRows=1)
            tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F5")),
                                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story += [tb, Spacer(1, 8)]
        elif t == "qa":
            qas.append(blk)
    if with_quiz and qas:
        story += [PageBreak(), heading("확인 문제", "h2", 0)]
        for i, q in enumerate(qas, 1):
            story.append(Paragraph(f"{i}. {escape(q['q'])}", ss["p"]))
        story += [PageBreak(), heading("정답", "h2", 0)]
        for i, q in enumerate(qas, 1):
            story.append(Paragraph(f"{i}. {escape(q['a'])}", ss["p"]))
    doc.multiBuild(story)
    from pypdf import PdfReader
    return {"pages": len(PdfReader(out_pdf).pages), "headings": doc.headings, "embedded": embedded}
