"""사용법: python -m engine.cli --kind budget --job freelancer --theme navy --out output"""
import argparse
import json
import os
from .builder import build_template
from .check import check_workbook
from .listing import make_listing


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="budget", help="budget | project | inventory")
    ap.add_argument("--job", default="freelancer", help="freelancer | shop_owner | student")
    ap.add_argument("--theme", default="navy")
    ap.add_argument("--out", default="output")
    ap.add_argument("--skip-recalc", action="store_true")
    a = ap.parse_args(argv)
    path = build_template(a.kind, a.job, a.theme, a.out)
    if a.skip_recalc:
        from .check import static_check
        chk = {"static": static_check(path), "ok": None}
    else:
        chk = check_workbook(path)
    with open(os.path.join(a.out, f"listing_{a.kind}_{a.job}.json"), "w", encoding="utf-8") as f:
        json.dump(make_listing(a.kind, a.job), f, ensure_ascii=False, indent=2)
    print(json.dumps({"file": path, "check": {k: v for k, v in chk.items() if k != "recalc_path"}}, ensure_ascii=False, indent=2))
    return 0 if chk["ok"] in (True, None) else 1


if __name__ == "__main__":
    raise SystemExit(main())
