import argparse
from .core import run, PREVIEW_SECONDS


def main(argv=None):
    p = argparse.ArgumentParser(prog="bgm_catalog",
                                description="BGM 카탈로그 사이트·미리듣기·라이선스 안내 초안 만들기")
    p.add_argument("csv", help="곡 정보 CSV 경로")
    p.add_argument("music_dir", help="음악 파일 폴더")
    p.add_argument("out_dir", help="결과를 저장할 폴더")
    p.add_argument("--title", default="BGM 라이브러리")
    p.add_argument("--seconds", type=int, default=PREVIEW_SECONDS)
    a = p.parse_args(argv)
    try:
        res = run(a.csv, a.music_dir, a.out_dir, a.title, a.seconds)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"[오류] {e}")
        return 2
    if not res["ok"]:
        print("[검증 실패] 아래를 고친 뒤 다시 실행하세요. (파일은 만들지 않았습니다)")
        for row, tid, msg in res["problems"]:
            print(f" - {row}행 {tid}: {msg}")
        return 1
    print(f"[완료] {res['tracks']}곡 처리. {a.out_dir}/index.html 을 열어 확인하세요.")
    return 0
