import argparse, json, os
from . import plan as P
from .render import render, RenderError


def main(argv=None):
    p = argparse.ArgumentParser(prog="shortform", description="제품 정보로 숏폼 장면표·자막·설명·무음 영상 만들기 (광고 표시 자동, 자동 업로드 없음)")
    p.add_argument("product"); p.add_argument("outdir"); p.add_argument("--video", action="store_true"); p.add_argument("--font")
    a = p.parse_args(argv)
    try:
        pl = P.make(P.load(a.product)); os.makedirs(a.outdir, exist_ok=True)
        json.dump(pl, open(os.path.join(a.outdir, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(os.path.join(a.outdir, "subtitles.srt"), "w", encoding="utf-8").write(P.srt(pl)); open(os.path.join(a.outdir, "caption.txt"), "w", encoding="utf-8").write(pl["caption"])
        for m in P.check(pl): print("[점검]", m)
        if a.video: render(pl, os.path.join(a.outdir, "video.mp4"), a.font); print("영상 만들었어요 (소리 없음)")
        print(f"장면 {len(pl['scenes'])}개, 총 {pl['total']}초"); return 0
    except (P.PlanError, RenderError, OSError) as e:
        print(f"[오류] {e}"); return 2
