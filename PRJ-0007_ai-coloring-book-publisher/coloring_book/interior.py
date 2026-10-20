"""내지 PDF 조립: 책 크기 페이지, 여백, 뒷면 빈 페이지, 최소 쪽수 채우기."""
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PT = 72.0


def build_interior(image_paths, out_pdf, trim_in, specs, blank_back=True, bleed=False):
    bleed_in = specs["bleed_in"] if bleed else 0.0
    # 블리드: 바깥쪽 가로 + 위/아래. 간단히 가로 한쪽, 세로 양쪽을 더한다.
    page_w = (trim_in[0] + bleed_in) * PT
    page_h = (trim_in[1] + 2 * bleed_in) * PT
    margin = specs["page_margin_in"] * PT
    c = canvas.Canvas(out_pdf, pagesize=(page_w, page_h))
    pages = 0

    def blank():
        nonlocal pages
        c.showPage(); pages += 1

    for p in image_paths:
        with Image.open(p) as im:
            im = im.convert("L")
            iw, ih = im.size
            box_w, box_h = page_w - 2 * margin, page_h - 2 * margin
            scale = min(box_w / iw, box_h / ih)
            dw, dh = iw * scale, ih * scale
            c.drawImage(ImageReader(im), (page_w - dw) / 2, (page_h - dh) / 2, dw, dh)
        blank()
        if blank_back:
            blank()
    # 최소 쪽수와 짝수 쪽수 맞추기
    while pages < specs["min_pages"] or pages % 2:
        blank()
    if pages > specs["max_pages"]:
        raise ValueError(f"쪽수 {pages}쪽이 최대 {specs['max_pages']}쪽을 넘습니다")
    c.save()
    return pages
