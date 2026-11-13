import argparse, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="dispatchq", description="문자 발송 준비(실제 발송 없음)")
    p.add_argument("templates"); p.add_argument("name"); p.add_argument("recipients")
    p.add_argument("--send-at", default="10:00"); p.add_argument("--out", default="outbox.jsonl")
    a = p.parse_args(argv)
    try:
        t = core.load_templates(a.templates)
        if a.name not in t: raise ValueError("없는 템플릿: " + a.name)
        out, skipped = core.build(t[a.name], core.read_recipients(a.recipients), a.send_at)
        with open(a.out, "w", encoding="utf-8") as f:
            for m in out: f.write(json.dumps(m, ensure_ascii=False) + "\n")
        print(f"준비 {len(out)}건 (SMS {sum(m['type']=='SMS' for m in out)}, LMS {sum(m['type']=='LMS' for m in out)}), 제외 {len(skipped)}건 → {a.out}")
        for n, w in skipped: print(f"[제외] {n}행: {w}")
        print("※ 실제 발송은 하지 않았습니다.")
    except (OSError, ValueError, KeyError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
