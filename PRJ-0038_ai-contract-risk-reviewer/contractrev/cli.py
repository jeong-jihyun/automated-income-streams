import argparse
from . import report


def main(argv=None):
    p = argparse.ArgumentParser(prog="contractrev", description="계약서 텍스트의 주의 조항을 쉬운 말로 표시 (법률 자문 아님)")
    p.add_argument("file", help="계약서 텍스트 파일(.txt)"); p.add_argument("--out")
    a = p.parse_args(argv)
    try:
        md = report.markdown(report.review(open(a.file, encoding="utf-8").read()))
        open(a.out, "w", encoding="utf-8").write(md) if a.out else print(md)
        return 0
    except (ValueError, OSError) as e:
        print(f"[오류] {e}"); return 2
