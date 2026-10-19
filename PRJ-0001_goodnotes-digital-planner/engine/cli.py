"""사용법: python -m engine.cli --year 2027 --lang ko --theme navy --out output"""
import argparse, json, os
from .config import PlannerConfig
from .planner import generate
from .validate import validate_pdf
from .preview import make_previews
from .copy_text import make_copy


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--week-start", default="monday")
    ap.add_argument("--lang", default="ko")
    ap.add_argument("--theme", default="navy")
    ap.add_argument("--no-weekly", action="store_true")
    ap.add_argument("--no-daily", action="store_true")
    ap.add_argument("--notes", type=int, default=5)
    ap.add_argument("--font", default="")
    ap.add_argument("--out", default="output")
    a = ap.parse_args(argv)
    cfg = PlannerConfig(year=a.year, week_start=a.week_start, lang=a.lang, theme=a.theme,
                        include_weekly=not a.no_weekly, include_daily=not a.no_daily,
                        note_pages=a.notes, font_path=a.font)
    pdf = os.path.join(a.out, f"planner_{a.year}_{a.lang}_{a.theme}.pdf")
    info = generate(cfg, pdf)
    check = validate_pdf(pdf)
    previews = make_previews(pdf, os.path.join(a.out, "previews"))
    text = make_copy(cfg, info)
    with open(os.path.join(a.out, "listing_copy.json"), "w", encoding="utf-8") as f:
        json.dump(text, f, ensure_ascii=False, indent=2)
    result = {"pdf": pdf, "check": check, "previews": previews}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if check["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
