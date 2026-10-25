"""연습 한 번 처리: 말한 내용(받아쓰기) → 목표와 비교 + 문법 점검 → 한글 피드백. 음성 파일은 저장하지 않는다."""
import datetime
import json
import os
from . import grammar, wer as W


def practice(target, said, today=None):
    rate, ops = W.wer(target, said)
    score = round((1 - rate) * 100)
    tips = [f"'{o[1]}' 대신 '{o[2]}'라고 들렸어요." if o[0] == "바뀜" else f"'{o[1]}'가 빠졌어요." if o[0] == "빠짐" else f"'{o[2]}'가 더 들어갔어요." for o in ops]
    g = grammar.check(said)
    grade = "아주 좋아요!" if score >= 90 else "좋아요, 조금만 더!" if score >= 70 else "천천히 다시 해 봐요."
    return {"date": today or datetime.date.today().isoformat(), "target": target, "said": said, "score": score, "grade": grade, "tips": tips, "grammar": g}


def transcribe_and_practice(target, audio_path, transcribe, today=None):
    """transcribe(audio_path)->글자 함수(음성 인식 서비스)를 꽂아 쓴다. 인식이 비면 점수를 매기지 않는다."""
    if not os.path.isfile(audio_path): raise FileNotFoundError(audio_path)
    said = (transcribe(audio_path) or "").strip()
    if not said: return {"error": "목소리를 알아듣지 못했어요. 조용한 곳에서 다시 말해 주세요."}
    return practice(target, said, today)


def log(path, result):
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    data.append({k: result[k] for k in ("date", "target", "said", "score")})
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def progress(path):
    if not os.path.exists(path): return {"count": 0}
    d = json.load(open(path, encoding="utf-8"))
    if not d: return {"count": 0}
    by = {}
    for r in d: by.setdefault(r["date"], []).append(r["score"])
    return {"count": len(d), "avg": round(sum(r["score"] for r in d) / len(d)), "days": {k: round(sum(v) / len(v)) for k, v in sorted(by.items())},
            "weak": [r["target"] for r in d if r["score"] < 70][-3:]}
