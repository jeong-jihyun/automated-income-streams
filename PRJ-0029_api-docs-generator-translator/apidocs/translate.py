"""번역 목록(카탈로그) 관리. 번역 자체는 AI 없이 하지 않는다: 용어집 적용 + 사람이 채우는 번역 칸 + 원문이 바뀌면 '낡음' 표시.
translator 함수를 넣으면(예: 사용자가 쓰는 번역 서비스) 빈 칸을 자동으로 채울 수 있다."""
import hashlib
import json
import re


def h(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def collect_strings(items):
    out = []
    def add(t):
        t = (t or "").strip()
        if t and t not in out: out.append(t)
    if "ops" in items:
        add(items["title"])
        for o in items["ops"]:
            add(o["summary"]); [add(p["desc"]) for p in o["params"]]; [add(d) for d in o["responses"].values()]
    else:
        add(items["doc"])
        for f in items["functions"]: add(f["doc"])
        for c in items["classes"]:
            add(c["doc"]); [add(m["doc"]) for m in c["methods"]]
    return out


def sync_catalog(catalog, strings):
    """catalog: {원문해시: {src, ko, status}} → 새 문장 추가, 바뀐/사라진 문장은 표시. (cat, 새로 추가, 사라짐) 반환."""
    cat = {k: dict(v) for k, v in catalog.items()}
    added = 0
    for s in strings:
        k = h(s)
        if k not in cat:
            cat[k] = {"src": s, "ko": "", "status": "번역 필요"}; added += 1
        elif cat[k]["status"] == "사용 안 함":
            cat[k]["status"] = "번역됨" if cat[k]["ko"] else "번역 필요"
    live = {h(s) for s in strings}
    gone = 0
    for k, v in cat.items():
        if k not in live and v["status"] != "사용 안 함":
            v["status"] = "사용 안 함"; gone += 1
    return cat, added, gone


def apply_glossary(text, glossary):
    """원문 속 용어를 한글 용어집 형태로 표시: 'order' → '주문(order)'. 이미 괄호 표기된 곳은 건드리지 않는다."""
    for en in sorted(glossary, key=len, reverse=True):
        text = re.sub(rf"(?<![\w(])({re.escape(en)})(?![\w)])", lambda m: f"{glossary[en]}({m.group(1)})", text, flags=re.I)
    return text


def fill(catalog, translator):
    n = 0
    for k, v in catalog.items():
        if v["status"] == "번역 필요":
            try: t = translator(v["src"])
            except Exception: continue
            if t and t.strip(): v["ko"], v["status"] = t.strip(), "번역됨(자동, 검수 필요)"; n += 1
    return n


def lookup(catalog, text):
    v = catalog.get(h((text or "").strip()))
    return v["ko"] if v and v["ko"] and v["status"] != "사용 안 함" else None


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        raise ValueError(f"번역 목록 JSON이 깨졌습니다: {path}")
