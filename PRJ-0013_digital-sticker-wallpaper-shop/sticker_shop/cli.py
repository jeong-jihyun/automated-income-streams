import argparse
import os
from PIL import Image
from . import checker, process, package
from .specs import load_specs


def _report(label, res):
    print(f"{label}: 합격 {len(res['ok'])}개 / 불합격 {len(res['bad'])}개")
    for n, pr in res["bad"].items():
        print(f" - {n}: " + "; ".join(pr))


def main(argv=None):
    p = argparse.ArgumentParser(prog="sticker_shop", description="디지털 스티커·배경화면 묶음 준비 (플랫폼 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--stickers", help="스티커 PNG 폴더")
        s.add_argument("--wallpapers", help="배경화면 원본 폴더")
        s.add_argument("--specs")
        if name == "build":
            s.add_argument("--out", required=True)
            s.add_argument("--name", default="디지털 스티커 팩")
            s.add_argument("--theme", default="감성")
    a = p.parse_args(argv)
    try:
        if not a.stickers and not a.wallpapers:
            raise ValueError("--stickers 또는 --wallpapers 중 하나는 필요합니다")
        specs = load_specs(a.specs)
        st = checker.check_stickers(a.stickers, specs) if a.stickers else None
        wp = checker.check_wallpapers(a.wallpapers, specs) if a.wallpapers else None
        if st: _report("스티커", st)
        if wp: _report("배경화면", wp)
        bad = (st and st["bad"]) or (wp and wp["bad"])
        if a.cmd == "check":
            return 1 if bad else 0
        if bad:
            print("[중단] 불합격 파일을 고치거나 빼고 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        out = a.out
        for d in ("stickers", "sheets", "wallpapers"):
            os.makedirs(os.path.join(out, d), exist_ok=True)
        n_st = n_sheets = 0
        sizes = specs["wallpaper"]["sizes"]
        if st:
            dims = []
            for n in st["ok"]:
                dims.append((n, *process.make_sticker(os.path.join(a.stickers, n), os.path.join(out, "stickers", n), specs["sticker"])))
            n_st = len(dims)
            sheets = process.pack_sheets(dims, specs["sheet"])
            for i, pl in enumerate(sheets, 1):
                process.render_sheet(pl, os.path.join(out, "stickers"), specs["sheet"], os.path.join(out, "sheets", f"sheet-{i:02d}.png"))
            n_sheets = len(sheets)
            package.sheet_preview(os.path.join(out, "sheets", "sheet-01.png"), os.path.join(out, "preview_stickers.png"),
                                  specs["preview"]["sheet_width"])
        if wp:
            made = []
            for n in wp["ok"]:
                made += process.make_wallpapers(os.path.join(a.wallpapers, n), os.path.join(out, "wallpapers"),
                                                os.path.splitext(n)[0], sizes, specs["wallpaper"]["jpeg_quality"])
            first = [m for m in made if m.endswith(f"_{sizes[0][0]}x{sizes[0][1]}.jpg")]
            package.wallpaper_preview(first[:4], os.path.join(out, "preview_wallpapers.png"), specs["preview"]["wallpaper_height"])
        package.guide_pdf(os.path.join(out, "guide.pdf"), a.name, n_st, n_sheets, sizes)
        open(os.path.join(out, "listing_draft.txt"), "w", encoding="utf-8").write(package.listing_draft(a.name, a.theme, n_st, sizes))
        package.make_zip(os.path.join(out, "sticker_pack.zip"), out)
        print(f"[완료] 스티커 {n_st}개, 시트 {n_sheets}장, 배경화면 {len(wp['ok']) if wp else 0}장 x {len(sizes)}크기 → {out}/sticker_pack.zip")
        print("Etsy·아이디어스 등록은 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
