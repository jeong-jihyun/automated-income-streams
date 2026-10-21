import argparse
import os
from . import parser, pdfgen, outputs


def main(argv=None):
    p = argparse.ArgumentParser(prog="exam_note", description="시험 요약노트 PDF 제작 보조 (플랫폼 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name); s.add_argument("--manuscript", required=True, help="요약 원고 .md")
        if name == "build":
            s.add_argument("--out", required=True)
            s.add_argument("--exam", default="시험")
            s.add_argument("--preview-pages", type=int, default=5)
            s.add_argument("--buyer", action="append", default=[], help="구매자 이름 (여러 번 가능)")
            s.add_argument("--font", help="한글 글꼴 파일(.ttf). 지정하면 PDF 안에 글꼴을 넣습니다")
    a = p.parse_args(argv)
    try:
        if not os.path.isfile(a.manuscript):
            raise FileNotFoundError(f"원고 파일이 없습니다: {a.manuscript}")
        text = open(a.manuscript, encoding="utf-8").read()
        if not text.strip():
            raise ValueError("원고가 비어 있습니다")
        blocks, problems = parser.parse(text)
        bad = parser.banned_phrases(text)
        print(f"점검: 블록 {len(blocks)}개 / 형식 문제 {len(problems)}건 / 금지 표현 {len(bad)}건")
        for ln, m in problems: print(f" - {ln}행: {m}" if ln else f" - {m}")
        for b in bad: print(f" - 금지 표현: '{b}' (합격 보장 같은 과장 표현은 쓰지 마세요)")
        if a.cmd == "check":
            return 1 if (problems or bad) else 0
        if problems or bad:
            print("[중단] 원고를 고친 뒤 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        os.makedirs(a.out, exist_ok=True)
        title = next(b["text"] for b in blocks if b["type"] == "h1")
        main_pdf = None
        for layout in pdfgen.LAYOUTS:
            path = os.path.join(a.out, f"note_{layout}.pdf")
            info = pdfgen.build_pdf(blocks, path, layout, a.font)
            if layout == "print":
                main_pdf, pages = path, info["pages"]
            print(f"  {pdfgen.LAYOUTS[layout]['label']}: {info['pages']}쪽 (글꼴 {'PDF에 포함' if info['embedded'] else '미포함(기본 한글 글꼴)'})")
        n = outputs.preview_pdf(main_pdf, os.path.join(a.out, "preview_free.pdf"), a.preview_pages)
        for buyer in a.buyer:
            safe = "".join(ch for ch in buyer if ch.isalnum() or ch in "-_") or "buyer"
            outputs.watermark_pdf(main_pdf, os.path.join(a.out, f"note_print_{safe}.pdf"), buyer)
        cov = outputs.cover_image(os.path.join(a.out, "cover.png"), title, a.exam, a.font)
        if cov["warning"]: print("경고:", cov["warning"])
        open(os.path.join(a.out, "listing_draft.txt"), "w", encoding="utf-8").write(outputs.listing_draft(title, a.exam, pages, n))
        print(f"[완료] 인쇄용/태블릿용 PDF, 맛보기 {n}쪽, 표지, 설명 초안, 구매자 워터마크 {len(a.buyer)}건 → {a.out}")
        print("클래스101·크몽 등록은 직접 하세요. 내용의 정확성은 사람이 검토하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
