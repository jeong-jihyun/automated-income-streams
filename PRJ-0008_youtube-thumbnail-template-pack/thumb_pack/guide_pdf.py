"""구매자 안내 PDF: 템플릿 링크 모음, 사용법, 글꼴 안내, 면책 문구."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

FONT = "HYSMyeongJo-Medium"
DISCLAIMER = "이 상품은 유튜브·구글의 공식 상품이 아니며, 두 회사와 제휴·후원 관계가 없습니다."


def build_guide(out_pdf, pack):
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    W, H = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)

    def page_title(t):
        c.setFont(FONT, 20); c.drawString(50, H - 70, t)

    # 1쪽: 표지
    page_title(pack["pack_name"])
    c.setFont(FONT, 12)
    c.drawString(50, H - 110, f"테마: {pack['theme']}")
    c.drawString(50, H - 135, "구매해 주셔서 감사합니다. 다음 쪽에서 템플릿 링크를 확인하세요.")
    c.drawString(50, 60, DISCLAIMER)
    c.showPage()
    # 2쪽: 링크 모음
    page_title("템플릿 링크 모음")
    y = H - 110
    c.setFont(FONT, 12)
    for it in pack["items"]:
        c.drawString(50, y, f"{it['title']}")
        c.setFillColorRGB(0, 0, 0.8)
        c.drawString(60, y - 16, it["canva_url"])
        c.linkURL(it["canva_url"], (55, y - 20, W - 50, y - 4), relative=0)
        c.setFillColorRGB(0, 0, 0)
        y -= 50
        if y < 100:
            c.showPage(); c.setFont(FONT, 12); y = H - 70
    c.showPage()
    # 3쪽: 사용법·글꼴
    page_title("사용 방법과 글꼴")
    c.setFont(FONT, 12)
    lines = ["1. 위 링크를 눌러 Canva에서 템플릿을 열고 '템플릿 사용'을 선택합니다.",
             "2. 글자와 이미지를 내 채널에 맞게 바꿉니다.",
             "3. 썸네일은 1280x720, 채널아트는 2560x1440 크기로 내보냅니다.",
             "", "글꼴 안내:"] + [f" - {f}" for f in pack.get("fonts", [])] + \
            ["", "유료 글꼴·유료 사진·유명 로고는 템플릿에 포함되어 있지 않습니다.", "", DISCLAIMER]
    y = H - 110
    for ln in lines:
        c.drawString(50, y, ln); y -= 22
    c.save()
    return 3
