import argparse
import csv
import io
from . import mask, detect


def main(argv=None):
    p = argparse.ArgumentParser(prog="pii_tool", description="문서·로그·CSV의 개인정보를 가립니다 (완벽하지 않으니 결과를 꼭 확인하세요)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("scan", "run"):
        s = sub.add_parser(n); s.add_argument("input")
        if n == "run":
            s.add_argument("--out", required=True); s.add_argument("--mode", default="token", choices=mask.MODES)
            s.add_argument("--key", help="hash 방식용 비밀 문구"); s.add_argument("--csv", action="store_true", help="CSV 파일(칸 단위로 처리)")
    a = p.parse_args(argv)
    try:
        text = open(a.input, encoding="utf-8-sig").read()
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"[오류] 파일을 읽을 수 없습니다: {a.input}"); return 2
    try:
        if a.cmd == "scan":
            for k, n in sorted(mask.anonymize(text)[1].items()): print(f"{detect.LABEL[k]}: {n}건")
            return 0
        total = {}
        if a.csv:
            rows = list(csv.reader(io.StringIO(text))); buf = io.StringIO(); w = csv.writer(buf)
            for r in rows:
                new = []
                for cell in r:
                    c, cnt = mask.anonymize(cell, a.mode, a.key)
                    new.append(c)
                    for k, v in cnt.items(): total[k] = total.get(k, 0) + v
                w.writerow(new)
            result = buf.getvalue()
        else:
            result, total = mask.anonymize(text, a.mode, a.key)
        open(a.out, "w", encoding="utf-8", newline="").write(result)
        print("가린 항목: " + (", ".join(f"{detect.LABEL[k]} {n}건" for k, n in sorted(total.items())) or "없음"))
        print("※ 이름·주소 등은 찾지 못할 수 있습니다. 공유 전에 결과를 눈으로 확인하세요.")
        return 0
    except mask.MaskError as e:
        print(f"[오류] {e}"); return 2
