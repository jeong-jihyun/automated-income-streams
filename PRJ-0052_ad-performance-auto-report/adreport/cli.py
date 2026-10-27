import argparse, json
from datetime import date
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="adreport", description="메타·네이버 광고 CSV → 주간 성과 보고서 (API 연결 없음)")
    p.add_argument("--meta"); p.add_argument("--naver"); p.add_argument("--week", required=True, help="주 시작일(월요일 아니어도 해당 주로 계산) YYYY-MM-DD"); p.add_argument("--map", help='열 이름 지정 JSON 파일 {"meta":{"spend":"열이름"}}'); p.add_argument("--out")
    a = p.parse_args(argv)
    try:
        if not (a.meta or a.naver): raise core.ReportError("--meta 또는 --naver 파일이 필요해요")
        mp = json.load(open(a.map, encoding="utf-8")) if a.map else {}
        rows = (core.load_csv(a.meta, "meta", mp.get("meta")) if a.meta else []) + (core.load_csv(a.naver, "naver", mp.get("naver")) if a.naver else [])
        md = core.report(rows, core.monday(date.fromisoformat(a.week)))
        open(a.out, "w", encoding="utf-8").write(md) if a.out else print(md); return 0
    except (core.ReportError, OSError, ValueError) as e:
        print(f"[오류] {e}"); return 2
