import argparse
from .core import prepare


def main(argv=None):
    p = argparse.ArgumentParser(prog="stock_prep", description="스톡 사진 업로드 준비 도구 (자동 업로드는 하지 않습니다)")
    p.add_argument("folder", help="사진 폴더")
    p.add_argument("memo_csv", help="메모 CSV (file, memo, title 선택)")
    p.add_argument("out_dir", help="결과 저장 폴더")
    p.add_argument("--settings", help="규격 설정 JSON (기본: 예시값)")
    a = p.parse_args(argv)
    try:
        r = prepare(a.folder, a.memo_csv, a.out_dir, a.settings)
    except (FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
    print(f"[완료] 전체 {r['total']}개 / 준비 {len(r['passed'])}개 / 문제 {len(r['failed'])}개 / 메모 없음 {len(r['no_memo'])}개")
    for n, ps in r["failed"]:
        print(f" - {n}: {'; '.join(ps)}")
    print(f"결과는 {a.out_dir} 의 report.md 를 보세요. 업로드는 직접 하세요.")
    return 1 if r["failed"] else 0
