import argparse
import os
from . import config, subs, preview, package


def main(argv=None):
    p = argparse.ArgumentParser(prog="video_preset", description="자막 스타일 묶음 준비 도구 (마켓 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--config", required=True)
        if name == "build":
            s.add_argument("--out", required=True)
            s.add_argument("--no-preview", action="store_true")
    a = p.parse_args(argv)
    try:
        cfg = config.load(a.config)
        problems, warnings = config.validate(cfg)
        print(f"점검: 스타일 {len(cfg['styles'])}종 / 문제 {len(problems)}건 / 경고 {len(warnings)}건")
        for m in problems: print(" - 문제:", m)
        for m in warnings: print(" - 경고:", m)
        if a.cmd == "check":
            return 1 if problems else 0
        if problems:
            print("[중단] 설정을 고친 뒤 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        out = a.out
        os.makedirs(os.path.join(out, "ass"), exist_ok=True); os.makedirs(os.path.join(out, "srt"), exist_ok=True)
        res = cfg["resolution"]
        files = []
        for s in cfg["styles"]:
            ap = os.path.join(out, "ass", f"{s['id']}.ass")
            open(ap, "w", encoding="utf-8").write(subs.build_ass(cfg["styles"], res, one_style_only=s["id"]))
            sp = os.path.join(out, "srt", f"{s['id']}.srt")
            open(sp, "w", encoding="utf-8").write(subs.build_srt(cfg["styles"], one_style_only=s["id"]))
            files += [f"ass/{s['id']}.ass", f"srt/{s['id']}.srt"]
        open(os.path.join(out, "ass", "all_styles.ass"), "w", encoding="utf-8").write(subs.build_ass(cfg["styles"], res))
        files.append("ass/all_styles.ass")
        has_preview = False
        if not a.no_preview:
            if preview.have_ass_filter():
                for s in cfg["styles"]:
                    m, g = preview.make_preview(os.path.join(out, "ass", f"{s['id']}.ass"), os.path.join(out, "previews"),
                                                s["id"], res, cfg["background"])
                    files += [f"previews/{s['id']}.mp4", f"previews/{s['id']}.gif"]
                has_preview = True
            else:
                print("경고: ffmpeg(ass 필터)가 없어 미리보기를 건너뜁니다.")
        open(os.path.join(out, "font_license_checklist.md"), "w", encoding="utf-8").write(package.font_checklist(cfg))
        package.guide_pdf(os.path.join(out, "guide.pdf"), cfg)
        open(os.path.join(out, "listing_draft.txt"), "w", encoding="utf-8").write(package.listing_draft(cfg, has_preview))
        files += ["font_license_checklist.md", "guide.pdf"]
        package.make_zip(os.path.join(out, "preset_pack.zip"), out, files)
        print(f"[완료] 스타일 {len(cfg['styles'])}종, 미리보기 {'있음' if has_preview else '없음'}, ZIP → {out}/preset_pack.zip")
        print("프리미어·캡컷에서 열어 보는 일과 마켓 등록은 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
