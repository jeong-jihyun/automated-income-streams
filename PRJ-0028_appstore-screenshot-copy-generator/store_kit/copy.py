"""스토어 문구 초안(템플릿 방식, AI 사용 안 함)과 글자 수·위험 표현·키워드 점검."""
from .spec import LIMITS, RISKY_CLAIMS, SCREENSHOT_LIMIT


class CopyError(ValueError):
    pass


def check_app(app):
    errs = []
    for k in ("app_name", "subtitle", "features", "keywords", "screens"):
        if not app.get(k):
            errs.append(f"'{k}' 항목이 비었습니다")
    return errs


def keyword_string(keywords, limit):
    seen, out = set(), []
    for k in (k.strip() for k in keywords):
        if k and k.lower() not in seen:
            seen.add(k.lower()); out.append(k)
    s = ",".join(out)
    while len(s) > limit and out:
        out.pop(); s = ",".join(out)
    return s, out


def draft(app):
    f = app["features"]
    short = f"{app['subtitle']} — " + ", ".join(f[:2])
    bullets = "\n".join(f"• {x}" for x in f)
    full = f"{app['app_name']}은(는) {app['subtitle']}를 돕는 앱입니다.\n\n주요 기능\n{bullets}\n\n문의와 의견은 앱 안의 문의하기로 보내 주세요."
    ks, used = keyword_string(app["keywords"], LIMITS["app_store"]["keywords"])
    return {"app_store": {"title": app["app_name"], "subtitle": app["subtitle"], "keywords": ks, "description": full,
                          "promo": f"{f[0]}. {app['subtitle']}."},
            "play": {"title": app["app_name"], "short": short, "full": full}, "keywords_used": used}


def validate(d, screens_n):
    problems = []
    for store, fields in d.items():
        if store not in LIMITS: continue
        for k, v in fields.items():
            lim = LIMITS[store].get(k)
            if lim and len(v) > lim:
                problems.append(f"{store}.{k}: {len(v)}자 (제한 {lim}자)")
            for bad in RISKY_CLAIMS:
                if bad.lower() in v.lower():
                    problems.append(f"{store}.{k}: 검증하기 어려운 과장 표현 '{bad}' — 근거 없이 쓰면 심사에서 거절될 수 있습니다")
    for store, (lo, hi) in SCREENSHOT_LIMIT.items():
        if not lo <= screens_n <= hi:
            problems.append(f"{store}: 스크린샷은 {lo}~{hi}장이어야 합니다 (현재 {screens_n}장)")
    return problems
