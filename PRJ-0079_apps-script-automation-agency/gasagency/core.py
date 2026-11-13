"""구글 앱스 스크립트 자동화 대행용 의뢰 점검: 견적 범위, 위험 표시, 권한(scope) 목록, 시작용 .gs 뼈대. 실제 배포는 하지 않는다."""
import csv

# 시간·단가는 예시 설정값이다(실제 단가가 아님). 바꿔 쓰는 곳은 이 한 곳.
HOURLY = 50000
BASE = {"dedupe": 3, "summary_mail": 4, "daily_trigger": 3, "form_to_sheet": 4}
SCOPES = {
    "dedupe": ["https://www.googleapis.com/auth/spreadsheets"],
    "summary_mail": ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/script.send_mail"],
    "daily_trigger": ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/script.scriptapp"],
    "form_to_sheet": ["https://www.googleapis.com/auth/forms", "https://www.googleapis.com/auth/spreadsheets"],
}
COLS = ["id", "client", "task", "sheets", "external_api", "personal_data", "urgency"]


def read(path):
    ok, bad, seen = [], [], set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        miss = [c for c in COLS if c not in (r.fieldnames or [])]
        if miss:
            raise ValueError("열이 없습니다: " + ", ".join(miss))
        for n, row in enumerate(r, start=2):
            try:
                t = row["task"].strip()
                if t not in BASE:
                    raise ValueError("지원하지 않는 작업: " + t)
                sheets = int(row["sheets"])
                if sheets < 1:
                    raise ValueError("sheets는 1 이상")
                api, pii = row["external_api"].strip(), row["personal_data"].strip()
                if api not in ("0", "1") or pii not in ("0", "1"):
                    raise ValueError("external_api/personal_data는 0 또는 1")
                u = row["urgency"].strip()
                if u not in ("normal", "rush"):
                    raise ValueError("urgency 값 오류")
                rid = row["id"].strip()
                if not rid or rid in seen:
                    raise ValueError("번호가 비었거나 중복")
                seen.add(rid)
                ok.append({"id": rid, "client": row["client"].strip(), "task": t, "sheets": sheets,
                           "api": api == "1", "pii": pii == "1", "rush": u == "rush"})
            except ValueError as e:
                bad.append((n, str(e)))
    return ok, bad


def estimate(q):
    h = BASE[q["task"]] + 2 * (q["sheets"] - 1) + (4 if q["api"] else 0) + (2 if q["pii"] else 0)
    if q["rush"]:
        h *= 1.3
    h = round(h, 1)
    return {"hours": h, "low": round(h * 0.8 * HOURLY, -3), "high": round(h * 1.3 * HOURLY, -3)}


def risks(q):
    r = []
    if q["pii"]:
        r.append("개인정보가 들어 있음: 시트 공유 범위와 보관 기간을 먼저 정하세요")
    if q["api"]:
        r.append("외부 서비스 호출(UrlFetchApp): 키 보관 위치와 호출 한도를 확인해야 합니다")
        r.append("외부 호출 권한(script.external_request)이 추가로 필요합니다")
    if q["task"] == "summary_mail":
        r.append("메일 발송 하루 한도가 있어 대량 발송에는 맞지 않습니다")
    if q["rush"]:
        r.append("급행: 시험할 시간이 줄어듭니다")
    return r


def scopes(q):
    s = list(SCOPES[q["task"]])
    if q["api"]:
        s.append("https://www.googleapis.com/auth/script.external_request")
    return s


GS = {
    "dedupe": """function dedupeRows() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('시트1');
  const rows = sheet.getDataRange().getValues();
  const seen = new Set();
  const keep = rows.filter(function (r, i) {
    if (i === 0) return true;
    const key = String(r[0]).trim();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  sheet.clearContents();
  sheet.getRange(1, 1, keep.length, keep[0].length).setValues(keep);
}
""",
    "summary_mail": """function sendSummary() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('시트1');
  const count = Math.max(sheet.getLastRow() - 1, 0);
  MailApp.sendEmail(Session.getActiveUser().getEmail(), '일일 요약', '오늘 기준 행 수: ' + count);
}
""",
    "daily_trigger": """function installDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('main').timeBased().everyDays(1).atHour(8).create();
}
function main() {
  Logger.log('매일 실행됨');
}
""",
    "form_to_sheet": """function onFormSubmit(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('응답정리');
  sheet.appendRow([new Date(), JSON.stringify(e.namedValues)]);
}
""",
}


def skeleton(task):
    return GS[task]


def report(ok, bad):
    out = []
    for q in ok:
        e = estimate(q)
        out.append(f"[{q['id']}] {q['client']} / {q['task']}: 약 {e['hours']}시간, {int(e['low']):,}~{int(e['high']):,}원 (예시 단가)")
        out += ["  주의: " + x for x in risks(q)]
    out += [f"[제외] {n}행: {w}" for n, w in bad]
    out.append("※ 단가·시간은 예시 설정입니다. 뼈대 코드는 구글 환경에서 실행해 보지 않았습니다.")
    return "\n".join(out)
