import argparse
import os
from . import analyze, cut, parse, report


def main(argv=None):
    p = argparse.ArgumentParser(prog="vidsum", description="자막으로 영상 요약·목차·하이라이트 구간 만들기 (영상 내용은 분석하지 않음)")
    p.add_argument("subtitle"); p.add_argument("--video"); p.add_argument("--out", required=True); p.add_argument("--window", type=int, default=60); p.add_argument("--highlights", type=int, default=3)
    a = p.parse_args(argv)
    try:
        cues = parse.parse(open(a.subtitle, encoding="utf-8-sig").read())
        segs = analyze.score(analyze.segments(cues, a.window)); hl = analyze.highlights(segs, a.highlights); summ = analyze.summary(segs)
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, "summary.md"), "w", encoding="utf-8").write(report.markdown(os.path.splitext(os.path.basename(a.subtitle))[0], segs, hl, summ))
        msg = f"[완료] summary.md (구간 {len(segs)}개, 하이라이트 {len(hl)}개)"
        if a.video: msg += f", 잘라 낸 영상 {len(cut.cut_all(a.video, hl, a.out))}개"
        print(msg); return 0
    except (parse.VideoError, OSError) as e:
        print(f"[오류] {e}"); return 2
