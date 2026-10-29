import argparse, json, os
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="clipcut", description="방송 자막에서 상품 홍보 클립 구간 고르기·자르기 (영상 내용 분석 없음, 업로드 없음)")
    p.add_argument("srt"); p.add_argument("--video"); p.add_argument("--out", default="clips"); p.add_argument("--keywords", default="", help="상품 키워드(쉼표)"); p.add_argument("--top", type=int, default=3); p.add_argument("--vertical", action="store_true")
    a = p.parse_args(argv)
    try:
        cues = core.parse_srt(open(a.srt, encoding="utf-8-sig").read()); kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
        clips = core.pick(cues, kws, a.top)
        if not clips: print("고를 만한 구간이 없어요(상품 키워드·가격·구매 유도 표현이 있는 15~45초 구간 없음)"); return 1
        os.makedirs(a.out, exist_ok=True)
        for i, c in enumerate(clips, 1):
            print(f"{i}. {c['start']:.1f}~{c['end']:.1f}초 ({c['len']}초) 점수 {c['score']}  {c['text'][:40]}" + ("".join(f"\n   ⚠ {f}" for f in c["flags"])))
            open(os.path.join(a.out, f"clip{i}.srt"), "w", encoding="utf-8").write(core.srt_for(c, cues))
            if a.video: core.cut(a.video, c, os.path.join(a.out, f"clip{i}.mp4"), a.vertical)
        json.dump(clips, open(os.path.join(a.out, "clips.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); return 0
    except (core.ClipError, OSError) as e:
        print(f"[오류] {e}"); return 2
