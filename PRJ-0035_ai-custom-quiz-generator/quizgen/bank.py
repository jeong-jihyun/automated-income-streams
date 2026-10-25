"""문제은행 읽기·검사. 문제: id, topic, grade, difficulty(1~3), q, choices, answer(번호 0부터), explanation."""
import json
import re


class QuizError(ValueError):
    pass


def norm(t):
    return re.sub(r"\W+", "", t.lower())


def check_item(it):
    for k in ("id", "topic", "grade", "difficulty", "q", "choices", "answer", "explanation"):
        if k not in it: raise QuizError(f"문제 정보 부족({it.get('id', '?')}): {k}")
    if not isinstance(it["choices"], list) or len(it["choices"]) < 2: raise QuizError(f"보기는 2개 이상({it['id']})")
    if len({norm(str(c)) for c in it["choices"]}) != len(it["choices"]): raise QuizError(f"같은 보기가 있습니다({it['id']})")
    if not isinstance(it["answer"], int) or not 0 <= it["answer"] < len(it["choices"]): raise QuizError(f"정답 번호가 보기 범위 밖({it['id']})")
    if it["difficulty"] not in (1, 2, 3): raise QuizError(f"난이도는 1~3({it['id']})")
    if not str(it["q"]).strip() or not str(it["explanation"]).strip(): raise QuizError(f"질문·해설이 비었습니다({it['id']})")


def load(path):
    try:
        items = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise QuizError(f"문제은행 JSON 오류: {e}")
    ids, qs = set(), set()
    for it in items:
        check_item(it)
        if it["id"] in ids: raise QuizError(f"id 중복: {it['id']}")
        if norm(it["q"]) in qs: raise QuizError(f"같은 질문이 중복: {it['id']}")
        ids.add(it["id"]); qs.add(norm(it["q"]))
    return items


def accept_ai_items(bank, new_items, verify=None):
    """AI가 만든 문제를 은행에 넣기 전 검사. 형식 오류·중복·정답 검증 실패는 거른다. (받은 것, 거른 이유) 반환."""
    ok, rejected = [], []
    ids = {b["id"] for b in bank}; qs = {norm(b["q"]) for b in bank}
    for it in new_items:
        try:
            check_item(it)
            if it["id"] in ids or norm(it["q"]) in qs: raise QuizError("중복")
            if verify and not verify(it): raise QuizError("정답 검증 실패")
        except (QuizError, TypeError) as e:
            rejected.append((it.get("id", "?") if isinstance(it, dict) else "?", str(e))); continue
        ok.append(it); ids.add(it["id"]); qs.add(norm(it["q"]))
    return ok, rejected
