import argparse
import os
from . import checker, interior, cover, metadata
from .specs import load_specs, trim_size


def main(argv=None):
    p = argparse.ArgumentParser(prog="coloring_book", description="컬러링북 제작 보조 (KDP 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--input", required=True, help="선화 이미지 폴더")
        s.add_argument("--trim", default="8.5x11")
        s.add_argument("--specs", help="규격 JSON (기본: config/kdp_specs.json 예시값)")
        if name == "build":
            s.add_argument("--out", required=True, help="결과 폴더")
            s.add_argument("--theme", default="나만의")
            s.add_argument("--paper", default="white")
            s.add_argument("--no-blank-back", action="store_true")
    a = p.parse_args(argv)
    try:
        specs = load_specs(a.specs)
        res = checker.check_folder(a.input, a.trim, specs)
        print(f"점검: 전체 {res['total']}장 / 합격 {len(res['ok'])}장 / 불합격 {len(res['bad'])}장")
        for n, pr in res["bad"].items():
            print(f" - {n}: " + "; ".join(pr))
        if a.cmd == "check":
            return 1 if res["bad"] else 0
        if res["bad"] or not res["ok"]:
            print("[중단] 불합격 이미지를 고치거나 빼고 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        os.makedirs(a.out, exist_ok=True)
        trim = trim_size(specs, a.trim)
        paths = [os.path.join(a.input, n) for n in res["ok"]]
        pages = interior.build_interior(paths, os.path.join(a.out, "interior.pdf"), trim, specs,
                                        blank_back=not a.no_blank_back)
        size = cover.build_cover(os.path.join(a.out, "cover.pdf"), f"{a.theme} 컬러링북", trim, pages, a.paper, specs)
        with open(os.path.join(a.out, "metadata_draft.txt"), "w", encoding="utf-8") as f:
            f.write(metadata.to_text(metadata.draft(a.theme, pages, specs)))
        print(f"[완료] 내지 {pages}쪽, 표지 {size['width_in']}x{size['height_in']}in (책등 {size['spine_in']}in) → {a.out}")
        print("업로드와 AI 사용 여부 선택은 KDP 사이트에서 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
