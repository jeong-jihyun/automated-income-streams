import argparse
import json
import os
import tempfile
from . import sheet, tts, audio, textbook, listing


def load_cfg(path=None):
    p = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    p = argparse.ArgumentParser(prog="audiobook_builder", description="회화 오디오북 제작 보조 (마켓 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--sheet", required=True, help="문장표 CSV")
        s.add_argument("--config")
        if name == "build":
            s.add_argument("--out", required=True)
            s.add_argument("--provider", help="silent | folder | edge-tts (기본: 설정 파일)")
            s.add_argument("--recordings", help="folder 제공자일 때 녹음 파일 폴더")
            s.add_argument("--gap", type=float, help="무음 간격(초)")
    a = p.parse_args(argv)
    try:
        cfg = load_cfg(a.config)
        rows = sheet.read_sheet(a.sheet)
        probs = sheet.check_rows(rows, cfg["max_text_len"])
        print(f"점검: 문장 {len(rows)}개 / 문제 {len(probs)}건")
        for ln, m in probs:
            print(f" - {ln}행: {m}")
        if a.cmd == "check":
            return 1 if probs else 0
        if probs:
            print("[중단] 문장표를 고친 뒤 다시 실행하세요. (결과 파일은 만들지 않았습니다)")
            return 1
        if a.gap is not None:
            cfg["gap_sec"] = a.gap
        name = a.provider or cfg["tts_provider"]
        provider = tts.get_provider(name, cfg, folder=a.recordings)
        os.makedirs(a.out, exist_ok=True)
        info = []
        with tempfile.TemporaryDirectory() as work:
            for i, (chap, crows) in enumerate(sheet.chapters(rows).items(), start=1):
                info.append((chap, crows, audio.build_chapter(i, chap, crows, provider, cfg, work, a.out)))
        with open(os.path.join(a.out, "toc.txt"), "w", encoding="utf-8") as f:
            f.write(audio.toc_text(info))
        pages = textbook.build_pdf(os.path.join(a.out, "textbook.pdf"), cfg["book_title"],
                                   [(n, r) for n, r, _ in info], cfg["pdf_font"])
        with open(os.path.join(a.out, "listing_draft.txt"), "w", encoding="utf-8") as f:
            f.write(listing.draft(cfg["book_title"], info, name))
        print(f"[완료] 챕터 {len(info)}개, 교재 {pages}쪽 → {a.out} (음성: {name})")
        if name == "silent":
            print("주의: silent 는 시험용 무음입니다. 판매용 음성이 아닙니다.")
        print("윌라·크몽 등록은 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"[오류] {e}")
        return 2
