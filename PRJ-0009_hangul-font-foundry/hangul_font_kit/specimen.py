"""시험지: 글자 견본표 PNG, 문장 미리보기, 견본 PDF."""
import math
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def glyph_sheet(ttf_path, chars, out_png, cell=96, cols=10):
    font = ImageFont.truetype(ttf_path, int(cell * 0.7))
    rows = max(1, math.ceil(len(chars) / cols))
    im = Image.new("RGB", (cols * cell, rows * cell), "white")
    d = ImageDraw.Draw(im)
    for i, ch in enumerate(chars):
        r, c = divmod(i, cols)
        d.rectangle((c * cell, r * cell, (c + 1) * cell - 1, (r + 1) * cell - 1), outline=(220, 220, 220))
        d.text((c * cell + cell * 0.15, r * cell + cell * 0.1), ch, font=font, fill="black")
    im.save(out_png)
    return im.size


def sentence_preview(ttf_path, sentence, available, out_png, size=64):
    shown = "".join(ch if (ch == " " or ch in available) else "□" for ch in sentence)
    missing = sorted({ch for ch in sentence if ch != " " and ch not in available})
    font = ImageFont.truetype(ttf_path, size)
    box = font.getbbox(shown)
    im = Image.new("RGB", (max(box[2] + 40, 200), size * 2), "white")
    ImageDraw.Draw(im).text((20, size // 2), shown, font=font, fill="black")
    im.save(out_png)
    return {"shown": shown, "missing": missing}


def specimen_pdf(out_pdf, sheet_png, sentence_png):
    W, H = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)
    for png in (sheet_png, sentence_png):
        with Image.open(png) as im:
            iw, ih = im.size
            s = min((W - 80) / iw, (H - 80) / ih)
            c.drawImage(ImageReader(im.convert("RGB")), 40, H - 40 - ih * s, iw * s, ih * s)
        c.showPage()
    c.save()
    return 2
