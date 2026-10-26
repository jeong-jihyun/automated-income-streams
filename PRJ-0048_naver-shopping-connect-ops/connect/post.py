"""상품 후기 글 초안 만들기 + 글 점검. 직접 써 본 경험(사용 일수·장점·아쉬운 점)을 사용자가 넣어야만 초안을 만든다 — 경험을 지어내지 않는다."""
import json, re

DISCLOSURE = "※ 이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 구매가 발생하면 일정액의 수수료를 제공받습니다."  # 예시 문구, 최신 공식 문구는 직접 확인
BAD = ["무조건", "100%", "최고의", "역대급", "완치", "치료", "기적", "부작용 없", "효과 보장"]
MIN_PHOTOS, MIN_CHARS = 3, 600


class PostError(ValueError):
    pass


def load(path):
    try: return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise PostError(f"파일을 읽지 못했습니다: {e}")


def make(f):
    miss = [k for k in ("product", "link", "who_for") if not f.get(k)]
    if miss: raise PostError("빠진 항목: " + ", ".join(miss))
    if not f.get("use_days") or f["use_days"] < 1: raise PostError("직접 사용한 일수(use_days)가 필요해요. 써 보지 않은 제품의 후기는 만들지 않아요")
    if not f.get("pros"): raise PostError("직접 느낀 장점(pros)을 1개 이상 적어 주세요")
    if not f.get("cons"): raise PostError("아쉬운 점(cons)도 1개 이상 필요해요. 장점만 있는 후기는 신뢰를 잃어요")
    li = lambda xs: "\n".join(f"- {x}" for x in xs)
    specs = f"\n## 기본 정보\n{li(f['specs'])}\n" if f.get("specs") else ""
    price = f"\n가격: {f['price']:,}원 ({f.get('price_date', '날짜 미확인')} 기준, 변동될 수 있어요)\n" if f.get("price") else ""
    body = (f"{DISCLOSURE}\n\n# {f['product']} {f['use_days']}일 써 본 후기\n{price}{specs}\n## 좋았던 점\n{li(f['pros'])}\n\n## 아쉬운 점\n{li(f['cons'])}\n\n"
            f"## 이런 분께 맞아요\n{f['who_for']}\n\n[사진 {MIN_PHOTOS}장 이상 직접 찍은 사진을 넣어 주세요]\n\n구매 링크: {f['link']}\n\n{DISCLOSURE}\n")
    return body


def check(text, photos=0):
    out = []
    if DISCLOSURE[:12] not in text[:200]: out.append(("고지", "글 맨 위(처음 200자 안)에 제휴 수수료 고지가 없어요"))
    if text.count("수수료") < 1: out.append(("고지", "수수료 문구가 없어요"))
    for w in BAD:
        if w in text: out.append(("과장", f"'{w}' 표현은 빼 주세요"))
    if photos < MIN_PHOTOS: out.append(("사진", f"직접 찍은 사진이 {MIN_PHOTOS}장 이상이어야 해요(현재 {photos}장)"))
    if len(re.sub(r"\s", "", text)) < MIN_CHARS: out.append(("분량", f"글이 너무 짧아요(공백 제외 {MIN_CHARS}자 이상 권장)"))
    if not re.search(r"아쉬|단점|불편", text): out.append(("균형", "아쉬운 점이 없어요"))
    return out
