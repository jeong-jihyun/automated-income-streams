"""글꼴 라이선스 목록, 구매자 안내 PDF, ZIP, 상품 설명 초안."""
import os
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

FONT = "HYSMyeongJo-Medium"
DISCLAIMER = "이 상품은 Adobe·ByteDance(캡컷) 등 편집 프로그램 회사의 공식 상품이 아니며 제휴 관계가 없습니다."


def font_checklist(cfg):
    listed = {f["name"].lower(): f for f in cfg["fonts"]}
    used = sorted({s["font"] for s in cfg["styles"]})
    lines = ["# 글꼴 라이선스 점검 목록 (판매 전 사람이 확인)", "",
             "| 글꼴 | 라이선스 | 받는 곳 | 묶음에 글꼴 파일 포함 가능 | 상태 |", "|---|---|---|---|---|"]
    for name in used:
        f = listed.get(name.lower())
        if not f:
            lines.append(f"| {name} | 정보 없음 | - | 확인 필요 | ⚠ 확인 필요 |")
            continue
        lic = f.get("license", "unknown"); red = str(f.get("redistribute", "unknown"))
        ok = lic not in ("", "unknown") and red.lower() == "true"
        lines.append(f"| {name} | {lic} | {f.get('source_url', '-')} | {red} | {'가능' if ok else '⚠ 확인 필요 (글꼴 파일은 넣지 말고 이름·받는 곳 링크만 안내)'} |")
    lines += ["", "※ 이 프로그램은 글꼴 파일을 묶음에 넣지 않습니다. 유료·출처 불명 글꼴은 사용하지 마세요."]
    return "\n".join(lines) + "\n"


def guide_pdf(out_pdf, cfg):
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    W, H = A4
    c = canvas.Canvas(out_pdf, pagesize=A4)
    pages = 0

    def page(title, lines):
        nonlocal pages
        c.setFont(FONT, 20); c.drawString(50, H - 70, title)
        c.setFont(FONT, 11)
        y = H - 110
        for ln in lines:
            c.drawString(50, y, ln); y -= 18
        pages += 1
        c.showPage()

    page(cfg["pack_name"], [f"테마: {cfg['theme']}", f"스타일 {len(cfg['styles'])}종", "",
                            "구매해 주셔서 감사합니다.", "", DISCLAIMER])
    page("프리미어 프로에서 쓰기 (예시 순서, 버전마다 화면 이름이 다를 수 있습니다)",
         ["1. 프로젝트에 ass/ 폴더의 자막 파일을 가져옵니다. (프리미어는 ASS를 직접 못 열 수 있어 SRT 사용을 권장)",
          "2. 자막 트랙에서 글꼴·크기·색을 안내서의 스타일 값과 같게 맞춥니다.",
          "3. 맞춘 스타일을 '스타일로 저장'하여 다음에 다시 씁니다.", "",
          "스타일 값:"] + [f" - {s['id']} {s['label']}: {s['font']} {s['size']}px {s['color']} 테두리 {s['outline']}"
                           for s in cfg["styles"]][:20])
    page("캡컷에서 쓰기 (예시 순서, 버전마다 화면 이름이 다를 수 있습니다)",
         ["1. 캡컷에서 SRT 자막 파일을 가져옵니다(자막 > 로컬 자막 가져오기).",
          "2. 자막을 선택하고 글꼴·크기·색·테두리를 스타일 값과 같게 맞춥니다.",
          "3. 맞춘 스타일을 '프리셋으로 저장'해 다음에 다시 씁니다.", "",
          "※ 프리미어·캡컷 전용 프리셋 파일은 이 묶음에 들어 있지 않습니다."])
    page("글꼴 안내", ["글꼴 파일은 묶음에 포함하지 않았습니다. font_license_checklist.md 를 참고하세요.", "",
                      "사용 글꼴:"] + [f" - {n}" for n in sorted({s['font'] for s in cfg['styles']})] + ["", DISCLAIMER])
    c.save()
    return pages


def listing_draft(cfg, has_preview):
    n = len(cfg["styles"])
    return "\n".join([
        f"제목: {cfg['pack_name']} — 편집용 {cfg['theme']} 자막 스타일 {n}종",
        f"설명: 영상 편집용 자막 스타일 {n}종(ASS/SRT), 미리보기{' 영상·GIF' if has_preview else ''}, 사용 안내서 PDF를 담았습니다. "
        "프리미어·캡컷에서 글꼴·색·크기를 같게 맞춰 쓰는 방식입니다. 편집 프로그램 회사의 공식 상품이 아닙니다.",
        f"태그: 자막 템플릿, {cfg['theme']} 자막, 캡컷 자막, 프리미어 자막, 자막 스타일", "",
        "[확인] 글꼴 라이선스: font_license_checklist.md",
        "[확인] Envato 등은 승인 기준(품질·독창성)이 따로 있습니다. 등록 전 공식 안내를 확인하세요 (여기서는 미확인).",
        "[확인] 미리보기에 음악·효과음·유명 영상 소스를 넣지 않았는지 확인하세요."]) + "\n"


def make_zip(zip_path, root, rel_paths):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for rp in rel_paths:
            z.write(os.path.join(root, rp), rp)
    return zip_path
