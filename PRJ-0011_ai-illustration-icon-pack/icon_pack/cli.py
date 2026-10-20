import argparse
import os
from . import checker, package
from .specs import load_specs


def main(argv=None):
    p = argparse.ArgumentParser(prog="icon_pack", description="아이콘 팩 준비 도구 (마켓 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--input", required=True, help="PNG 폴더")
        s.add_argument("--specs")
        if name == "build":
            s.add_argument("--out", required=True)
            s.add_argument("--name", default="아이콘 팩")
            s.add_argument("--theme", default="미니멀")
    a = p.parse_args(argv)
    try:
        specs = load_specs(a.specs)
        r = checker.check_folder(a.input, specs)
        print(f"점검: 전체 {r['total']}개 / 합격 {len(r['ok'])}개 / 불합격 {len(r['bad'])}개")
        for n, pr in r["bad"].items():
            print(f" - {n}: " + "; ".join(pr))
        if a.cmd == "check":
            return 1 if r["bad"] else 0
        if r["bad"]:
            print("[중단] 불합격 파일을 고치거나 빼고 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        os.makedirs(a.out, exist_ok=True)
        package.resize_all(a.input, r["ok"], a.out, specs["sizes"])
        sheet = package.contact_sheet(a.input, r["ok"], os.path.join(a.out, "preview_sheet.png"), specs["contact_sheet"])
        lic = package.license_pdf(os.path.join(a.out, "license_guide.pdf"), a.name, len(r["ok"]), specs["sizes"])
        draft = os.path.join(a.out, "listing_draft.txt")
        with open(draft, "w", encoding="utf-8") as f:
            f.write(package.listing_draft(a.name, len(r["ok"]), specs["sizes"], a.theme))
        z = package.make_zip(a.out, os.path.join(a.out, "icon_pack.zip"), [lic, os.path.join(a.out, "preview_sheet.png")])
        print(f"[완료] 아이콘 {len(r['ok'])}개 × {len(specs['sizes'])}개 크기, ZIP {os.path.basename(z)} → {a.out}")
        print("마켓 등록은 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
