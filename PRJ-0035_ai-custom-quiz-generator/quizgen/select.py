"""약점 맞춤 선택: 정답률이 낮은 주제를 더 자주, 막 맞힌 문제는 피한다. seed로 재현."""
import random


def accuracy(profile, topic):
    t = profile.get("topics", {}).get(topic)
    return None if not t or t["total"] == 0 else t["right"] / t["total"]


def weak_topics(profile, below=0.6, min_total=2):
    return sorted(k for k, v in profile.get("topics", {}).items() if v["total"] >= min_total and v["right"] / v["total"] < below)


def pick(bank, profile, n, grade, seed, recent_ok=()):
    pool = [b for b in bank if b["grade"] == grade and b["id"] not in set(recent_ok)]
    if n < 1: raise ValueError("문제 수는 1 이상")
    if not pool: return []
    rng = random.Random(seed)
    w = {b["id"]: 1.0 + (3.0 * (1 - accuracy(profile, b["topic"])) if accuracy(profile, b["topic"]) is not None else 1.0) for b in pool}   # 못 푼 주제일수록 가중치 큼
    chosen, left = [], list(pool)
    while left and len(chosen) < n:
        x = rng.choices(left, weights=[w[b["id"]] for b in left])[0]; chosen.append(x); left.remove(x)
    return chosen
