import argparse, sys
from pathlib import Path
from . import core


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sfx-pack", description="효과음 팩 빌더 (자동 업로드 기능 없음)")
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--theme", default="Sound")
    ap.add_argument("--prefix", default="sfx")
    ap.add_argument("--settings")
    a = ap.parse_args(argv)
    try:
        st = core.load_settings(a.settings)
        res = core.build_pack(a.src, a.out, a.prefix, st)
        if not res["rows"]:
            print("처리된 소리가 없습니다.")
            return 1
        for r in res["rows"]:
            print(r["file"], f"{r['seconds']}s", r["issues"] or "OK")
        for n, e in res["skipped"]:
            print("건너뜀:", n, e)
        text, warns = core.description_draft(a.theme, res["rows"])
        Path(a.out, "description.txt").write_text(text, encoding="utf-8")
        core.make_demo(Path(a.out) / "wav", Path(a.out) / "demo.mp3", st)
        for w in warns:
            print(w)
        print("※ 사람 귀로 직접 들어보고, 마켓에는 직접 업로드하세요.")
        return 0
    except (NotADirectoryError, RuntimeError, ValueError) as e:
        print("오류:", e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
