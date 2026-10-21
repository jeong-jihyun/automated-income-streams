"""맛보기 PDF, 구매자별 워터마크 PDF, 표지 이미지, 상품 설명 초안."""
import io
import os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from PIL import Image, ImageDraw, ImageFont
from .parser import banned_phrases


def preview_pdf(src, dst, n_pages):
    r = PdfReader(src)
    if n_pages < 1:
        raise ValueError("맛보기 쪽수는 1 이상")
    n = min(n_pages, len(r.pages))
    w = PdfWriter()
    for i in range(n):
        w.add_page(r.pages[i])
    with open(dst, "wb") as f:
        w.write(f)
    return n


def watermark_pdf(src, dst, buyer, font_name="HYSMyeongJo-Medium"):
    """모든 쪽에 구매자 이름을 연한 회색 대각선으로 넣는다."""
    if not buyer.strip():
        raise ValueError("구매자 이름이 비어 있습니다")
    try:
        pdfmetrics.getFont(font_name)
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium")); font_name = "HYSMyeongJo-Medium"
    r = PdfReader(src); w = PdfWriter()
    for page in r.pages:
        pw, ph = float(page.mediabox.width), float(page.mediabox.height)
        buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(pw, ph))
        c.saveState(); c.setFillColorRGB(0.6, 0.6, 0.6); c.setFillAlpha(0.18); c.setFont(font_name, 34)
        c.translate(pw / 2, ph / 2); c.rotate(40); c.drawCentredString(0, 0, f"{buyer} 전용")
        c.restoreState(); c.save(); buf.seek(0)
        page.merge_page(PdfReader(buf).pages[0])
        w.add_page(page)
    with open(dst, "wb") as f:
        w.write(f)
    return len(r.pages)


def find_cover_font(font_path=None):
    for p in ([font_path] if font_path else []) + ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                                                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
        if p and os.path.isfile(p):
            return p
    return None


def cover_image(dst, title, subtitle, font_path=None):
    fp = find_cover_font(font_path)
    img = Image.new("RGB", (1200, 1600), (31, 56, 100))
    d = ImageDraw.Draw(img)
    d.rectangle((60, 60, 1140, 1540), outline=(220, 230, 245), width=6)
    try:
        if fp:
            big = ImageFont.truetype(fp, 84, index=1) if fp.endswith(".ttc") else ImageFont.truetype(fp, 84)
            small = ImageFont.truetype(fp, 40, index=1) if fp.endswith(".ttc") else ImageFont.truetype(fp, 40)
        else:
            raise OSError("no font")
        warn = None
    except OSError:
        big = small = ImageFont.load_default()
        warn = "한글 글꼴 파일을 찾지 못해 표지 글자가 깨질 수 있습니다 (--font 로 글꼴 파일 지정)"
    y = 500
    line = ""
    for ch in title:  # 단순 줄바꿈
        if d.textlength(line + ch, font=big) > 960:
            d.text((120, y), line, font=big, fill="white"); y += 110; line = ""
        line += ch
    d.text((120, y), line, font=big, fill="white")
    d.text((120, 1350), subtitle, font=small, fill=(220, 230, 245))
    img.save(dst)
    return {"size": img.size, "warning": warn}


def listing_draft(title, exam, n_pages, preview_pages):
    text = "\n".join([
        f"제목: {title} — {exam} 핵심 요약노트 PDF",
        f"설명: 직접 정리한 {exam} 요약노트입니다. 목차, 핵심 용어 박스, 암기표, 확인 문제와 정답이 들어 있습니다. "
        f"총 {n_pages}쪽, 무료 맛보기 {preview_pages}쪽 제공. 인쇄용(A4)과 태블릿용 두 가지 여백으로 드립니다.",
        f"태그: {exam}, 요약노트, 시험 정리, 핵심 요약, PDF", "",
        "[확인] 기출문제·교재·강의 내용을 그대로 옮기지 않고 직접 쓴 요약만 담았는지 확인하세요.",
        "[확인] 시험 기관의 로고·상표를 쓰지 않았는지 확인하세요. 내용의 정확성은 사람이 검토해야 합니다.",
        "[확인] 클래스101·크몽의 전자책 등록 규정과 수수료를 등록 전에 공식 안내에서 확인하세요 (여기서는 미확인)."]) + "\n"
    found = banned_phrases(text)
    assert not found, found
    return text
