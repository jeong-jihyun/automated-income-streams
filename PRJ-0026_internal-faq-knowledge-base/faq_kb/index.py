"""사내 FAQ 검색: 한글 형태소 분석기 없이 '글자 2-gram + 단어'로 색인하고 BM25로 순위를 매긴다. 외부 AI·인터넷을 쓰지 않는다."""
import csv
import json
import math
import re
from collections import Counter
from datetime import date, datetime

K1, B = 1.5, 0.75
STOP = {"어떻게", "하나요", "알려주세요", "있나요", "인가요", "해요", "해야", "합니다", "주세요", "무엇", "어디", "언제"}


class KbError(ValueError):
    pass


def tokens(text):
    out = []
    for w in re.findall(r"[가-힣]+|[A-Za-z0-9]+", (text or "").lower()):
        if w in STOP: continue
        if re.match(r"[가-힣]", w):
            out.append(w)
            out += [w[i:i + 2] for i in range(len(w) - 1)] if len(w) >= 2 else []
        else:
            out.append(w)
    return out


def load_csv(path):
    try:
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    except FileNotFoundError:
        raise KbError(f"파일이 없습니다: {path}")
    need = {"id", "question", "answer"}
    if not rows or not need <= set(rows[0]):
        raise KbError("CSV에 id,question,answer 열이 필요합니다 (tags,dept,updated는 선택)")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise KbError("id가 중복입니다")
    for r in rows:
        if not (r["question"] or "").strip() or not (r["answer"] or "").strip():
            raise KbError(f"id {r['id']}: 질문 또는 답변이 비었습니다")
        r["dept"] = (r.get("dept") or "all").strip() or "all"
        r["tags"] = [t.strip() for t in (r.get("tags") or "").split(";") if t.strip()]
        r["updated"] = (r.get("updated") or "").strip()
        if r["updated"]:
            try: datetime.strptime(r["updated"], "%Y-%m-%d")
            except ValueError: raise KbError(f"id {r['id']}: updated는 YYYY-MM-DD 형식")
    return rows


class Index:
    def __init__(self, docs):
        self.docs = docs
        self.tf = [Counter(tokens(d["question"]) * 2 + tokens(d["answer"]) + tokens(" ".join(d["tags"])) * 2) for d in docs]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.len) / len(docs)) if docs else 0
        df = Counter(w for t in self.tf for w in t)
        n = len(docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def search(self, query, dept="all", top=3, min_score=1.0):
        """(문서, 점수) 목록. 점수가 min_score 미만이면 '답 없음'으로 보고 비워 돌려준다. 다른 부서 전용 문서는 제외."""
        q = tokens(query)
        res = []
        for i, d in enumerate(self.docs):
            if d["dept"] not in ("all", dept): continue
            s = 0.0
            for w in set(q):
                f = self.tf[i].get(w, 0)
                if f: s += self.idf[w] * f * (K1 + 1) / (f + K1 * (1 - B + B * self.len[i] / self.avg))
            if s > 0: res.append((d, round(s, 2)))
        res.sort(key=lambda x: (-x[1], x[0]["id"]))
        return [r for r in res[:top] if r[1] >= min_score]


def stale(docs, today, days=365):
    return [d["id"] for d in docs if d["updated"] and (today - datetime.strptime(d["updated"], "%Y-%m-%d").date()).days > days]


def missing_dates(docs):
    return [d["id"] for d in docs if not d["updated"]]


def near_duplicates(docs, threshold=0.6):
    sets = [set(tokens(d["question"])) for d in docs]
    out = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            u = sets[i] | sets[j]
            if u and len(sets[i] & sets[j]) / len(u) >= threshold:
                out.append((docs[i]["id"], docs[j]["id"]))
    return out


def save(docs, path):
    json.dump(docs, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def load_index(path):
    try:
        return Index(json.load(open(path, encoding="utf-8")))
    except FileNotFoundError:
        raise KbError(f"색인 파일이 없습니다: {path} (먼저 build 하세요)")
