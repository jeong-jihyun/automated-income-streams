import argparse
import json
import os
from . import extract, render, translate


def main(argv=None):
    p = argparse.ArgumentParser(prog="apidocs", description="코드/OpenAPI에서 문서 만들기 + 번역 목록 관리 (자동 번역은 하지 않음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("source", help=".py 또는 openapi .json"); b.add_argument("--out", required=True)
    b.add_argument("--catalog", default="translations.json"); b.add_argument("--glossary")
    a = p.parse_args(argv)
    try:
        if not os.path.isfile(a.source): raise extract.DocError(f"파일이 없습니다: {a.source}")
        text = open(a.source, encoding="utf-8").read()
        items = extract.parse_openapi(text) if a.source.endswith(".json") else extract.parse_python(text, os.path.splitext(os.path.basename(a.source))[0])
        cat, added, gone = translate.sync_catalog(translate.load(a.catalog), translate.collect_strings(items))
        if a.glossary:
            g = json.load(open(a.glossary, encoding="utf-8"))
            for v in cat.values():                                  # 빈 번역 칸에는 용어집 힌트를 남긴다(번역 아님)
                if v["status"] == "번역 필요": v["hint"] = translate.apply_glossary(v["src"], g)
        json.dump(cat, open(a.catalog, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, "docs_en.md"), "w", encoding="utf-8").write(render.render(items, "en"))
        open(os.path.join(a.out, "docs_ko.md"), "w", encoding="utf-8").write(render.render(items, "ko", cat))
        todo = sum(1 for v in cat.values() if v["status"] == "번역 필요")
        print(f"[완료] docs_en.md, docs_ko.md → {a.out} / 새 문장 {added}, 사라진 문장 {gone}, 번역 필요 {todo}")
        if todo: print(f"{a.catalog} 의 빈 'ko' 칸을 채우고 다시 실행하면 한글 문서에 반영됩니다. (자동 번역은 하지 않았습니다)")
        return 0
    except (extract.DocError, ValueError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
