"""댓글 자동 답변 후보 만들기. 스팸·부정 댓글은 자동 답변하지 않고 '사람이 볼 것'으로 분류한다. 실제 게시는 하지 않는다."""
import json


class RuleError(ValueError):
    pass


def load_rules(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise RuleError(f"규칙 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise RuleError(f"JSON 형식 오류: {e}")
    if not cfg.get("rules"):
        raise RuleError("rules가 비었습니다")
    for r in cfg["rules"]:
        if not r.get("keywords") or not r.get("reply"):
            raise RuleError(f"규칙 '{r.get('name')}'에 keywords와 reply가 필요합니다")
        if "{name}" not in r["reply"]:
            pass
    cfg.setdefault("block_words", []); cfg.setdefault("negative_words", []); cfg.setdefault("max_replies_per_hour", 20)
    return cfg


def classify(cfg, comment):
    text = (comment.get("text") or "").lower()
    if any(w.lower() in text for w in cfg["block_words"]):
        return {"action": "ignore", "reason": "스팸 의심"}
    if any(w.lower() in text for w in cfg["negative_words"]):
        return {"action": "human", "reason": "부정/불만 — 사람이 직접 답하세요"}
    for r in cfg["rules"]:
        if any(k.lower() in text for k in r["keywords"]):
            return {"action": "reply", "reason": r["name"], "reply": r["reply"].replace("{name}", comment.get("user") or "고객")}
    return {"action": "human", "reason": "맞는 규칙 없음"}


def plan(cfg, comments, replied_ids=(), replies_last_hour=0):
    """댓글 목록 → 처리 계획. 이미 답한 댓글은 건너뛰고, 시간당 답변 한도를 넘으면 나머지는 사람에게 넘긴다."""
    out, budget = [], cfg["max_replies_per_hour"] - replies_last_hour
    for c in comments:
        if c["id"] in replied_ids:
            continue
        d = classify(cfg, c)
        if d["action"] == "reply":
            if budget <= 0:
                d = {"action": "human", "reason": "시간당 답변 한도 초과"}
            else:
                budget -= 1
        out.append({"id": c["id"], **d})
    return out
