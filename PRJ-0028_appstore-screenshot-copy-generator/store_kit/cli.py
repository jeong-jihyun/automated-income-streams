import argparse
import json
import os
from . import copy, shots, spec


def main(argv=None):
    p = argparse.ArgumentParser(prog="store_kit", description="앱 스토어 스크린샷·문구 초안 (스토어 등록은 직접 하세요)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("check", "build"):
        s = sub.add_parser(n); s.add_argument("--app", required=True)
        if n == "build":
            s.add_argument("--out", required=True); s.add_argument("--sizes", default="ios_6.7,play_phone"); s.add_argument("--font")
    a = p.parse_args(argv)
    try:
        app = json.load(open(a.app, encoding="utf-8")); base = os.path.dirname(os.path.abspath(a.app))
        errs = copy.check_app(app)
        if errs: raise copy.CopyError("; ".join(errs))
        d = copy.draft(app); problems = copy.validate(d, len(app["screens"]))
        for x in problems: print(" - " + x)
        if a.cmd == "check":
            print(f"점검 완료: 문제 {len(problems)}건"); return 1 if problems else 0
        if problems: print("(문제를 고친 뒤 다시 실행하면 더 좋습니다. 이미지는 계속 만듭니다)")
        font = shots.find_font(a.font)
        if not font: print("경고: 한글 글꼴을 찾지 못해 글자가 깨질 수 있습니다 (--font 로 글꼴 지정)")
        sizes = [x for x in a.sizes.split(",") if x]
        bad = [x for x in sizes if x not in spec.SIZES]
        if bad: raise shots.ShotError(f"모르는 규격: {', '.join(bad)} (가능: {', '.join(spec.SIZES)})")
        os.makedirs(a.out, exist_ok=True)
        for sz in sizes:
            for i, sc in enumerate(app["screens"], 1):
                shots.make_shot(os.path.join(base, sc["image"]), sc["headline"], sc.get("bg", "#333333"), spec.SIZES[sz], font).save(os.path.join(a.out, f"{sz}_{i:02d}.png"))
        json.dump(d, open(os.path.join(a.out, "store_copy.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[완료] 스크린샷 {len(sizes) * len(app['screens'])}장, store_copy.json → {a.out}")
        print("규격·글자 수 제한은 알려진 값입니다. 스토어 등록 전에 공식 안내로 확인하고, 직접 등록하세요.")
        return 0
    except (copy.CopyError, shots.ShotError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
