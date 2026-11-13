"""엑셀 VBA 매크로 납품 전 점검: 소스 글(.bas/.txt)을 정규식으로 훑어 위험·불편 패턴을 알려 준다. 매크로를 실행하거나 만들어 주지는 않는다."""
import re

H, M, L = "높음", "중간", "낮음"
ORDER = {H: 0, M: 1, L: 2}

# (이름, 정규식, 등급, 설명)  — 한 줄 단위로 주석·문자열을 뺀 코드에서 찾는다
RULES = [
    ("외부 프로그램 실행", r"\bShell\b\s*[\(\"]|\bShell\b\s+\w", H, "Shell 로 다른 프로그램을 실행합니다"),
    ("파일 삭제", r"\bKill\b\s+|\bRmDir\b|\.DeleteFile\b|\.DeleteFolder\b", H, "파일·폴더를 지웁니다"),
    ("외부 객체 생성", r"\bCreateObject\s*\(", H, "WScript·FileSystemObject·XMLHTTP 등 외부 개체를 만듭니다"),
    ("API 선언", r"^\s*(Public\s+|Private\s+)?Declare\s+(PtrSafe\s+)?(Function|Sub)\b", H, "Windows API 를 직접 부릅니다"),
    ("자동 실행", r"\bSub\s+(Auto_Open|Workbook_Open|Document_Open)\b", M, "파일을 열면 저절로 실행됩니다"),
    ("오류 무시", r"\bOn\s+Error\s+Resume\s+Next\b", M, "오류를 숨깁니다(원인 찾기 어려움)"),
    ("화면 갱신 끄기", r"\bScreenUpdating\s*=\s*False\b", L, "끄고 다시 켜지 않으면 화면이 멈춘 듯 보입니다"),
    ("고정 경로", r"[A-Za-z]:\\[^\"\s]+", L, "내 컴퓨터에만 있는 경로일 수 있습니다"),
    ("Select·Activate 사용", r"\.(Select|Activate)\b", L, "느리고 깨지기 쉬운 방식입니다"),
]


def strip_line(line):
    """문자열 안의 내용은 유지하되(경로 찾기용) 주석(' 또는 Rem)만 뺀다. 문자열 속 ' 는 주석으로 보지 않는다."""
    out, inq = [], False
    for i, ch in enumerate(line):
        if ch == '"':
            inq = not inq
        if ch == "'" and not inq:
            break
        out.append(ch)
    s = "".join(out)
    return "" if re.match(r"^\s*Rem\b", s, re.I) else s


def scan(text):
    found, code_lines = [], 0
    lines = text.splitlines()
    for n, raw in enumerate(lines, start=1):
        code = strip_line(raw)
        if not code.strip():
            continue
        code_lines += 1
        for name, pat, sev, why in RULES:
            if re.search(pat, code, re.I):
                found.append({"line": n, "name": name, "sev": sev, "why": why})
    if not re.search(r"^\s*Option\s+Explicit\b", "\n".join(strip_line(l) for l in lines), re.I | re.M):
        found.append({"line": 0, "name": "Option Explicit 없음", "sev": M, "why": "변수 이름 오타를 못 잡아 줍니다"})
    pw = [n for n, l in enumerate(lines, 1) if re.search(r"password\s*[:=]+\s*\"[^\"]+\"", l, re.I)]
    for n in pw:
        found.append({"line": n, "name": "암호가 코드에 적힘", "sev": H, "why": "글자로 적힌 암호는 파일을 연 사람이 볼 수 있습니다"})
    found.sort(key=lambda f: (ORDER[f["sev"]], f["line"]))
    return found, code_lines


def verdict(found):
    h = sum(1 for f in found if f["sev"] == H)
    return "납품 전 확인 필요" if h else ("주의 사항 있음" if found else "발견된 것 없음")


def report(name, found, code_lines):
    out = [f"{name}: 코드 {code_lines}줄, 발견 {len(found)}건 → {verdict(found)}"]
    for f in found:
        where = f"{f['line']}줄" if f["line"] else "전체"
        out.append(f"- [{f['sev']}] {where} {f['name']}: {f['why']}")
    out.append("※ 글자 패턴만 훑는 검사입니다. 없다고 안전하다는 뜻이 아니며, 매크로를 실행해 보지 않았습니다.")
    return "\n".join(out)
