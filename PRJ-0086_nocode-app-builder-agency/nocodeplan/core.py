"""노코드 앱 제작 의뢰 사양(JSON) 점검: 데이터·화면·역할이 서로 맞는지, 노코드로 하기 어려운 요구가 있는지, 작업 시간 범위를 알려 준다. 앱을 만들지는 않는다."""
import json

TYPES = {"text", "number", "date", "bool", "phone", "email", "image", "choice"} 
PII = {"phone", "email"}
HOURLY = 50000  # 예시 단가
ACTIONS = {"list", "create", "edit", "delete", "view"}


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if not isinstance(d, dict) or not isinstance(d.get("tables"), dict) or not isinstance(d.get("screens"), list):
        raise ValueError("app, roles, tables(객체), screens(목록)가 필요합니다")
    return d


def check(d):
    """(오류, 주의) 문구 목록. 오류는 사양이 모순인 것, 주의는 사람이 판단할 것."""
    err, warn = [], []
    roles = set(d.get("roles", [])); tables = d["tables"]
    for t, spec in tables.items():
        for f, typ in (spec.get("fields") or {}).items():
            if typ.startswith("ref:"):
                if typ[4:] not in tables:
                    err.append(f"표 '{t}'의 칸 '{f}'가 없는 표 '{typ[4:]}'를 가리킴")
            elif typ not in TYPES:
                err.append(f"표 '{t}'의 칸 '{f}': 알 수 없는 종류 '{typ}'")
    seen, used_tables, used_roles = set(), set(), set()
    for s in d["screens"]:
        n = s.get("name", "")
        if not n or n in seen:
            err.append(f"화면 이름이 비었거나 중복: '{n}'")
        seen.add(n)
        if s.get("table") not in tables:
            err.append(f"화면 '{n}'이 없는 표 '{s.get('table')}'를 사용")
        else:
            used_tables.add(s["table"])
        for r in s.get("roles", []):
            if r not in roles:
                err.append(f"화면 '{n}'이 없는 역할 '{r}'를 사용")
            used_roles.add(r)
        bad = set(s.get("actions", [])) - ACTIONS
        if bad:
            err.append(f"화면 '{n}': 알 수 없는 동작 {sorted(bad)}")
    for t in tables:
        if t not in used_tables:
            warn.append(f"표 '{t}'는 어떤 화면에서도 쓰이지 않음")
    for r in sorted(roles - used_roles):
        warn.append(f"역할 '{r}'가 볼 수 있는 화면이 없음")
    for s in d["screens"]:
        t = tables.get(s.get("table"), {}); pii = [f for f, typ in (t.get("fields") or {}).items() if typ in PII]
        if pii and len(s.get("roles", [])) > 1 and "list" in s.get("actions", []):
            warn.append(f"화면 '{s['name']}': 연락처({', '.join(pii)})가 여러 역할에게 목록으로 보임")
    n = d.get("needs", {})
    if n.get("payment"): warn.append("결제 필요: 쓰려는 노코드 도구의 결제 연동 지원 여부와 수수료를 먼저 확인")
    if n.get("offline"): warn.append("오프라인 사용 필요: 노코드 도구는 대체로 약함")
    if n.get("realtime"): warn.append("실시간 갱신 필요: 도구·요금제별 제한 확인")
    if n.get("users", 0) > 1000: warn.append(f"사용자 {n['users']}명: 도구의 사용자·행 수 한도와 요금 확인")
    if n.get("external_apis", 0) > 3: warn.append(f"외부 서비스 연동 {n['external_apis']}개: 노코드만으로는 복잡해질 수 있음")
    return err, warn


def estimate(d):
    h = 0.0
    for t in d["tables"].values():
        h += 2 + 0.5 * len(t.get("fields") or {})
    h += 3 * len(d["screens"]); n = d.get("needs", {})
    h += 6 * bool(n.get("payment")) + 4 * bool(n.get("realtime")) + 5 * bool(n.get("offline")) + 2 * n.get("external_apis", 0)
    return {"hours": round(h, 1), "low": round(h * 0.8 * HOURLY, -3), "high": round(h * 1.4 * HOURLY, -3)}


def report(d):
    err, warn = check(d); e = estimate(d)
    out = [f"# {d.get('app', '이름 없음')} 점검", f"표 {len(d['tables'])}개, 화면 {len(d['screens'])}개, 역할 {len(d.get('roles', []))}개",
           f"작업 약 {e['hours']}시간, {int(e['low']):,}~{int(e['high']):,}원 (예시 단가)"]
    out += ["", "## 고쳐야 할 것" if err else "## 고쳐야 할 것: 없음"] + [f"- {x}" for x in err]
    out += ["", "## 확인할 것" if warn else "## 확인할 것: 없음"] + [f"- {x}" for x in warn]
    out += ["", "※ 사양 글자만 점검합니다. 실제 노코드 도구에서 만들어 보지 않았고 시간·단가는 예시입니다."]
    return "\n".join(out)
