import argparse
import json
import os
from . import charset, checker, builder, specimen, docs_draft


def _cfg(path):
    p = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "font.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    p = argparse.ArgumentParser(prog="hangul_font_kit", description="한글 폰트 제작 보조 (마켓 자동 등록은 하지 않습니다)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("charset"); s.add_argument("--out", required=True)
    for name in ("check", "build"):
        s = sub.add_parser(name)
        s.add_argument("--glyphs", required=True, help="U+AC00.svg 형식 SVG 폴더")
        s.add_argument("--config")
        if name == "build":
            s.add_argument("--out", required=True)
            s.add_argument("--allow-missing", action="store_true", help="빠진 글자가 있어도 만듦(시험용)")
    a = p.parse_args(argv)
    try:
        if a.cmd == "charset":
            n = charset.write_csv(a.out)
            print(f"[완료] 필수 글자 {n}자 목록 → {a.out}")
            return 0
        cfg = _cfg(a.config)
        r = checker.check_folder(a.glyphs, cfg)
        print(f"점검: 읽은 글자 {len(r['found'])}자 / 필수 {r['required']}자 / 빠진 글자 {len(r['missing'])}자 / 문제 {len(r['problems'])}건")
        for n, m in r["problems"]:
            print(f" - {n}: {m}")
        for n, m in r["warnings"]:
            print(f" - (경고) {n}: {m}")
        if a.cmd == "check":
            return 1 if (r["problems"] or r["missing"]) else 0
        if r["problems"]:
            print("[중단] 문제 있는 글리프를 고친 뒤 다시 실행하세요.")
            return 1
        if r["missing"] and not a.allow_missing:
            print("[중단] 빠진 글자가 있습니다. 시험용으로만 만들려면 --allow-missing 을 쓰세요.")
            return 1
        os.makedirs(a.out, exist_ok=True)
        ttf = os.path.join(a.out, f"{cfg['family_name']}.ttf")
        n = builder.build_ttf(r["found"], cfg, ttf)
        chars = [chr(cp) for cp in sorted(r["found"])]
        sheet = os.path.join(a.out, "glyph_sheet.png")
        specimen.glyph_sheet(ttf, chars, sheet)
        sen = specimen.sentence_preview(ttf, cfg["sample_sentence"], set(chars), os.path.join(a.out, "sentence.png"))
        specimen.specimen_pdf(os.path.join(a.out, "specimen.pdf"), sheet, os.path.join(a.out, "sentence.png"))
        with open(os.path.join(a.out, "license_draft.md"), "w", encoding="utf-8") as f:
            f.write(docs_draft.license_table())
        with open(os.path.join(a.out, "product_draft.md"), "w", encoding="utf-8") as f:
            f.write(docs_draft.product_draft(cfg["family_name"], n, r["required"], cfg["sample_sentence"]))
        print(f"[완료] TTF {n}자 → {ttf}")
        if sen["missing"]:
            print(f"미리보기 문장에서 빠진 글자: {''.join(sen['missing'])}")
        print("마켓 입점·심사·등록은 직접 하세요.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
