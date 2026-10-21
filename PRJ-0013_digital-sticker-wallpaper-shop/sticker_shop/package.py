"""미리보기, 사용 안내 PDF, 상품 설명 초안, ZIP."""
import glob
import os
import zipfile
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

FONT = "HYSMyeongJo-Medium"


def sheet_preview(sheet_png, out_png, width):
    with Image.open(sheet_png) as im:
        im = im.convert("RGBA")
        h = int(im.height * width / im.width)
        bg = Image.new("RGBA", (width, h), (235, 235, 240, 255))
        bg.alpha_composite(im.resize((width, h), Image.LANCZOS))
        bg.convert("RGB").save(out_png)
    return (width, h)


def wallpaper_preview(paths, out_png, height):
    ims = []
    for p in paths:
        with Image.open(p) as im:
            im = im.convert("RGB"); w = int(im.width * height / im.height)
            ims.append(im.resize((w, height), Image.LANCZOS))
    gap = 24
    W = sum(i.width for i in ims) + gap * (len(ims) + 1)
    out = Image.new("RGB", (W, height + 2 * gap), (245, 245, 245))
    x = gap
    for i in ims:
        out.paste(i, (x, gap)); x += i.width + gap
    out.save(out_png)
    return out.size


def guide_pdf(out_pdf, pack_name, n_stickers, n_sheets, sizes):
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    W, H = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)
    c.setFont(FONT, 20); c.drawString(50, H - 70, f"{pack_name} — 사용 안내")
    c.setFont(FONT, 12)
    lines = [f"구성: 낱개 스티커 {n_stickers}개(투명 PNG), 스티커 시트 {n_sheets}장, 배경화면 {len(sizes)}가지 크기", "",
             "굿노트에서 쓰기 (예시 순서, 화면 이름은 앱 버전에 따라 다를 수 있습니다):",
             "1. 낱개 스티커 PNG를 사진 앨범이나 파일에 저장합니다.",
             "2. 굿노트 노트에서 이미지 추가로 PNG를 불러옵니다.",
             "3. 크기와 위치를 손가락으로 조절합니다.", "",
             "배경화면: 기기 크기에 맞는 파일을 고르세요.", *[f" - {w}x{h}" for w, h in sizes], "",
             "개인 사용 안내: 파일을 다시 판매하거나 나눠주지 마세요. (예시 문구 — 판매 전 직접 정하세요)"]
    y = H - 110
    for ln in lines:
        c.drawString(50, y, ln); y -= 20
    c.save()
    return 1


def listing_draft(pack_name, theme, n_stickers, sizes):
    return "\n".join([
        f"제목: {pack_name} — {theme} 디지털 스티커 {n_stickers}개 + 배경화면",
        f"설명: 투명 배경 스티커 {n_stickers}개, 정리된 스티커 시트, 배경화면 {len(sizes)}가지 크기를 담았습니다. 다이어리 꾸미기용입니다.",
        f"태그: 디지털 스티커, 굿노트 스티커, {theme} 스티커, 배경화면, 다꾸", "",
        "[확인] Etsy 는 AI 생성물 표기·제작 방법 공개를 요구할 수 있습니다. 등록 전에 공식 정책을 확인하세요 (여기서는 미확인).",
        "[확인] 캐릭터·브랜드·유명 그림체를 닮은 그림, 폰트·소재의 상업 이용 라이선스를 확인하세요.",
        "[확인] 굿노트와 실제 폰에서 보이는 모습은 사람이 직접 확인하세요."]) + "\n"


def make_zip(zip_path, root):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for sub in ("stickers", "sheets", "wallpapers"):
            for p in sorted(glob.glob(os.path.join(root, sub, "*"))):
                z.write(p, os.path.relpath(p, root))
        for f in ("guide.pdf", "preview_stickers.png", "preview_wallpapers.png"):
            if os.path.exists(os.path.join(root, f)):
                z.write(os.path.join(root, f), f)
    return zip_path
