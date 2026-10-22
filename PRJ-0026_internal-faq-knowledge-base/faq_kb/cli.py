import argparse
from datetime import date
from . import index as ix


def main(argv=None):
    p = argparse.ArgumentParser(prog="faq_kb", description="사내 FAQ 검색 (인터넷·외부 AI 사용 안 함)")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--csv", required=True); b.add_argument("--index", default="kb.json")
    q = sub.add_parser("ask"); q.add_argument("question"); q.add_argument("--index", default="kb.json"); q.add_argument("--dept", default="all")
    c = sub.add_parser("check"); c.add_argument("--csv", required=True); c.add_argument("--days", type=int, default=365); c.add_argument("--today")
    a = p.parse_args(argv)
    try:
        if a.cmd == "build":
            docs = ix.load_csv(a.csv); ix.save(docs, a.index); print(f"{len(docs)}개 항목 색인 완료 → {a.index}")
        elif a.cmd == "ask":
            hits = ix.load_index(a.index).search(a.question, a.dept)
            if not hits:
                print("관련 답변을 찾지 못했습니다. 담당자에게 문의하세요.")
            for d, s in hits:
                print(f"[{s}] Q. {d['question']}\n    A. {d['answer']}" + (f"  (최종 수정 {d['updated']})" if d["updated"] else ""))
        else:
            docs = ix.load_csv(a.csv); today = date.fromisoformat(a.today) if a.today else date.today()
            for i in ix.stale(docs, today, a.days): print(f" - {i}번: {a.days}일 넘게 수정되지 않았습니다")
            for i in ix.missing_dates(docs): print(f" - {i}번: 수정일이 없습니다")
            for x, y in ix.near_duplicates(docs): print(f" - {x}번과 {y}번 질문이 비슷합니다")
            print(f"점검 완료: {len(docs)}개")
        return 0
    except (ix.KbError, ValueError) as e:
        print(f"[오류] {e}"); return 2
