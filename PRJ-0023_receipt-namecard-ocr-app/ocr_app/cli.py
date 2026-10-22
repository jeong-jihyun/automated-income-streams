import argparse
import os
import tempfile
from . import engine, export, parse


def main(argv=None):
    p = argparse.ArgumentParser(prog="ocr_app", description="영수증·명함 사진/글자 → CSV (결과는 사람이 확인하세요)")
    p.add_argument("kind", choices=["receipt", "namecard"])
    p.add_argument("inputs", nargs="+", help="이미지(.png/.jpg) 또는 OCR 결과 글자(.txt)")
    p.add_argument("--out", required=True); p.add_argument("--lang", default="kor+eng")
    a = p.parse_args(argv)
    parsed = []
    try:
        for f in a.inputs:
            if not os.path.isfile(f):
                raise engine.OcrError(f"파일이 없습니다: {f}")
            if f.lower().endswith(".txt"):
                text = open(f, encoding="utf-8").read()
            else:
                with tempfile.TemporaryDirectory() as td:
                    text = engine.read_text(f, a.lang, td)
            r = (parse.parse_receipt if a.kind == "receipt" else parse.parse_namecard)(text)
            parsed.append(r)
            print(f"{os.path.basename(f)}: " + ("; ".join(r["warnings"]) or "항목 모두 찾음"))
        csv_text = (export.receipts_csv if a.kind == "receipt" else export.cards_csv)(parsed)
        open(a.out, "w", encoding="utf-8-sig", newline="").write(csv_text)
        print(f"[완료] {len(parsed)}건 → {a.out} (인식 결과는 틀릴 수 있으니 원본과 대조하세요)")
        return 0
    except engine.OcrError as e:
        print(f"[오류] {e}")
        return 2
