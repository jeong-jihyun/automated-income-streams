import argparse
import os
from . import checker, preview, guide_pdf, listing
from .specs import load_specs, load_pack


def main(argv=None):
    p = argparse.ArgumentParser(prog="thumb_pack", description="썸네일 템플릿 묶음 준비 도구 (Canva·Gumroad 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--input", required=True, help="PNG/JPG 폴더")
        s.add_argument("--specs")
        if name == "build":
            s.add_argument("--config", required=True, help="pack.json")
            s.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        specs = load_specs(a.specs)
        res = checker.check_folder(a.input, specs)
        print(f"점검: 전체 {res['total']}개 / 합격 {len(res['ok'])}개 / 불합격 {len(res['bad'])}개")
        for n, pr in res["bad"].items():
            print(f" - {n}: " + "; ".join(pr))
        if a.cmd == "check":
            return 1 if res["bad"] else 0
        if res["bad"] or not res["ok"]:
            print("[중단] 불합격 파일을 고친 뒤 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        pack = load_pack(a.config)
        os.makedirs(a.out, exist_ok=True)
        sheet = preview.contact_sheet(a.input, res["ok"], os.path.join(a.out, "preview_sheet.png"), specs)
        guide_pdf.build_guide(os.path.join(a.out, "buyer_guide.pdf"), pack)
        counts = {k: sum(1 for n in res["ok"] if n.startswith(k + "_")) for k in ("thumb", "art")}
        with open(os.path.join(a.out, "listing_draft.txt"), "w", encoding="utf-8") as f:
            f.write(listing.to_text(listing.draft(pack, counts)))
        print(f"[완료] 미리보기 {sheet['cols']}열x{sheet['rows']}행, 안내 PDF, 상품 설명 초안 → {a.out}")
        print("Canva·Gumroad 등록은 사이트에서 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
