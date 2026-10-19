import argparse, sys
from pathlib import Path
from . import core


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kakao-checker", description="이모티콘 규격 검수 도구 (자동 제출 기능 없음)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="폴더 규격 검사")
    c.add_argument("folder")
    c.add_argument("--preset", default="kakao_static")
    c.add_argument("--presets-file")
    r = sub.add_parser("resize", help="규격 크기로 맞춤(새 폴더에 저장)")
    r.add_argument("folder")
    r.add_argument("out")
    r.add_argument("--preset", default="kakao_static")
    r.add_argument("--presets-file")
    n = sub.add_parser("rename", help="순번 이름 정리")
    n.add_argument("folder")
    n.add_argument("--prefix", default="emoticon")
    n.add_argument("--apply", action="store_true", help="실제로 바꿈(기본은 미리보기)")
    t = sub.add_parser("plan", help="구성표 CSV 만들기")
    t.add_argument("--count", type=int, default=32)
    d = sub.add_parser("draft", help="제안 문구 초안")
    d.add_argument("name")
    d.add_argument("concept")
    d.add_argument("personality")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            res = core.check_folder(a.folder, core.load_preset(a.preset, a.presets_file))
            print(core.format_report(res))
            return 0 if res["ok"] else 1
        if a.cmd == "resize":
            done = core.resize_all(a.folder, a.out, core.load_preset(a.preset, a.presets_file))
            print(f"{len(done)}개 변환 -> {a.out}")
            return 0
        if a.cmd == "rename":
            for o, nw in core.rename_files(a.folder, a.prefix, dry_run=not a.apply):
                print(f"{o} -> {nw}")
            if not a.apply:
                print("(미리보기입니다. --apply 를 붙이면 실제로 바뀝니다)")
            return 0
        if a.cmd == "plan":
            print(core.make_plan_table(a.count))
            return 0
        if a.cmd == "draft":
            print(core.proposal_draft(a.name, a.concept, a.personality))
            return 0
    except (NotADirectoryError, KeyError) as e:
        print("오류:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
