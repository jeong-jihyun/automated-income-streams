"""크기 변환, 미리보기 모음, ZIP, 라이선스 PDF, 상품 설명 초안."""
import math
import os
import zipfile
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

FONT = "HYSMyeongJo-Medium"


def resize_all(folder, names, out_dir, sizes):
    made = []
    for s in sizes:
        d = os.path.join(out_dir, "png", str(s)); os.makedirs(d, exist_ok=True)
        for n in names:
            with Image.open(os.path.join(folder, n)) as im:
                im.convert("RGBA").resize((s, s), Image.LANCZOS).save(os.path.join(d, n))
            made.append(os.path.join(d, n))
    return made


def contact_sheet(folder, names, out_path, cs):
    cols, cell, gap = cs["columns"], cs["cell"], cs["gap"]
    rows = math.ceil(len(names) / cols)
    W, H = cols * cell + (cols + 1) * gap, rows * cell + (rows + 1) * gap
    sheet = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        with Image.open(os.path.join(folder, n)) as im:
            im = im.convert("RGBA").resize((cell, cell), Image.LANCZOS)
            sheet.alpha_composite(im, (gap + c * (cell + gap), gap + r * (cell + gap)))
    sheet.convert("RGB").save(out_path)
    return {"cols": cols, "rows": rows, "size": sheet.size}


LICENSE_LINES = ["이 아이콘 팩의 사용 범위 (초안 — 공개 전 전문가 확인 필요)",
                 "- 구매자는 개인·상업 프로젝트(웹, 앱, 인쇄물)에 사용할 수 있습니다. (예시)",
                 "- 아이콘 파일 자체를 다시 판매하거나 배포할 수 없습니다. (예시)",
                 "- 이 팩은 AI 도구의 도움을 받아 제작되었습니다. 마켓의 AI 표시 규정을 따릅니다.",
                 "- 유명 캐릭터·브랜드 로고를 닮은 그림은 포함하지 않았습니다."]


def license_pdf(out_pdf, pack_name, count, sizes):
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    W, H = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)
    c.setFont(FONT, 20); c.drawString(50, H - 80, f"{pack_name} — 사용 안내")
    c.setFont(FONT, 12)
    y = H - 120
    c.drawString(50, y, f"포함: 아이콘 {count}개 × 크기 {', '.join(map(str, sizes))}px (PNG, 투명 배경)")
    y -= 30
    for ln in LICENSE_LINES:
        c.drawString(50, y, ln); y -= 22
    c.save()
    return out_pdf


def make_zip(out_dir, zip_path, extra_files):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        png_root = os.path.join(out_dir, "png")
        for root, _, files in os.walk(png_root):
            for f in sorted(files):
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, out_dir))
        for p in extra_files:
            z.write(p, os.path.basename(p))
    return zip_path


def listing_draft(pack_name, count, sizes, theme):
    return "\n".join([
        f"제목: {pack_name} — 일관된 스타일 {theme} 아이콘 {count}개",
        f"설명: 투명 배경 PNG 아이콘 {count}개를 {', '.join(map(str, sizes))}px 크기로 담았습니다. 미리보기 모음 이미지와 사용 안내 PDF 포함.",
        f"태그: {theme} 아이콘, icon pack, png 아이콘, 투명 배경, 웹 디자인, 앱 디자인", "",
        "[확인] 사용한 AI 도구의 약관(상업 이용·재판매)을 확인하세요.",
        "[확인] Creative Market, Freepik 의 AI 생성물 표시·허용 규칙을 등록 전에 공식 안내에서 확인하세요 (여기서는 미확인).",
        "[확인] 유명 캐릭터·브랜드 로고를 닮은 그림이 없는지 직접 확인하세요."]) + "\n"
