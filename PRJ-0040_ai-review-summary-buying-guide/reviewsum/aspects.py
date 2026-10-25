"""장점·단점 뽑기(키워드 방식, AI 아님). 항목별(배송·가격·품질 …) 칭찬/불만 낱말이 든 리뷰를 센다."""
ASPECTS = {"배송": ["배송", "택배", "포장", "도착"], "가격": ["가격", "가성비", "비싸", "저렴", "값"], "품질": ["품질", "마감", "내구", "튼튼", "허술", "불량"],
           "사이즈": ["사이즈", "크기", "작아", "커요", "핏", "헐렁"], "소음": ["소음", "소리", "시끄", "조용"], "디자인": ["디자인", "색상", "색깔", "예쁘", "이쁘"], "사용감": ["사용", "편해", "편리", "불편", "무겁", "가벼"]}
GOOD = ["좋", "만족", "추천", "빠르", "저렴", "튼튼", "조용", "편해", "편리", "예쁘", "이쁘", "가볍", "훌륭", "가성비"]
BAD = ["별로", "실망", "불량", "느리", "비싸", "허술", "시끄", "불편", "무겁", "작아", "헐렁", "아쉽", "나빠", "고장", "냄새", "파손"]


def polarity(text):
    g, b = sum(text.count(w) for w in GOOD), sum(text.count(w) for w in BAD)
    return "good" if g > b else "bad" if b > g else "neutral"


def analyze(rows):
    res = {a: {"good": [], "bad": []} for a in ASPECTS}
    for r in rows:
        for a, keys in ASPECTS.items():
            if any(k in r["text"] for k in keys):
                p = polarity(r["text"]) if r["rating"] in (2, 3, 4) else ("good" if r["rating"] == 5 else "bad")
                if p in ("good", "bad"): res[a][p].append(r["text"])
    return res
