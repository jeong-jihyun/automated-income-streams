import argparse
import os
from . import analyze as an, render


def main(argv=None):
    p = argparse.ArgumentParser(prog="survey_report", description="설문 CSV 자동 보고서 (유료 AI API 사용 안 함)")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--csv", required=True)
    b = sub.add_parser("build"); b.add_argument("--csv", required=True); b.add_argument("--out", required=True)
    b.add_argument("--title", default="설문 결과 보고서"); b.add_argument("--keep-pii", action="store_true", help="개인정보 열을 보고서에 남김")
    a = p.parse_args(argv)
    try:
        cols, rows = an.load(a.csv)
        res = an.analyze(cols, rows, drop_pii=not getattr(a, "keep_pii", False))
        print(f"응답 {res['n']}건 / 열 {len(cols)}개 / 개인정보 의심 열: {', '.join(res['pii']) or '없음'}")
        for col in res["columns"]:
            print(f" - {col['name']}: {col['type']} (빈칸 {col['missing']})")
        if a.cmd == "check":
            return 0
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, "report.html"), "w", encoding="utf-8").write(render.html_report(res, a.title))
        render.pdf_report(res, a.title, os.path.join(a.out, "report.pdf"))
        print(f"[완료] report.html, report.pdf → {a.out}")
        if res["dropped"]:
            print("개인정보로 보이는 열은 보고서에서 뺐습니다:", ", ".join(res["dropped"]))
        return 0
    except an.SurveyError as e:
        print(f"[오류] {e}")
        return 2
