import argparse
from datetime import date
from . import plans, leads


def main(argv=None):
    p = argparse.ArgumentParser(prog="telecom", description="요금제 비교와 상담 신청 기록 (실제 전송 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("compare"); c.add_argument("plans"); c.add_argument("--gb", type=float); c.add_argument("--call", type=int, default=0); c.add_argument("--discount", type=float, default=0.0, help="할인율 0~1 (예: 0.25)"); c.add_argument("--device", type=int, default=0, help="월 단말 할부금"); c.add_argument("--months", type=int, default=24); c.add_argument("--today")
    l = s.add_parser("lead"); l.add_argument("file"); l.add_argument("--name"); l.add_argument("--phone"); l.add_argument("--plan"); l.add_argument("--agree-collect", action="store_true"); l.add_argument("--agree-third", action="store_true"); l.add_argument("--agree-marketing", action="store_true")
    r = s.add_parser("report"); r.add_argument("file")
    d = s.add_parser("delete"); d.add_argument("file"); d.add_argument("--phone", required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "compare":
            if not 0 <= a.discount < 1: raise plans.PlanError("할인율은 0 이상 1 미만이어야 해요")
            print(plans.render(plans.rank(plans.load(a.plans), a.gb, a.call, a.discount, a.device, a.months, date.fromisoformat(a.today) if a.today else None), a.months)); return 0
        if a.cmd == "lead":
            print("동의 항목:"); [print(" -", v) for v in leads.CONSENT_TEXT.values()]
            leads.save(a.file, a.name, a.phone, a.plan, a.agree_collect, a.agree_third, a.agree_marketing); print("이 컴퓨터의 파일에 저장했어요(제휴사로 전송하지 않아요)"); return 0
        if a.cmd == "report": print(leads.report(a.file)); return 0
        print(f"{leads.delete(a.file, a.phone)}건 삭제했어요"); return 0
    except (plans.PlanError, leads.LeadError, ValueError, OSError) as e:
        print(f"[오류] {e}"); return 2
