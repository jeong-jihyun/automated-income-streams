"""상품 제목·설명·태그 초안 (복사해서 쓰는 용도). 자동 등록은 하지 않는다."""

CANVA_CHECK = ["Canva 콘텐츠 라이선스와 템플릿 판매 규정을 판매 전에 공식 안내에서 확인하세요 (Canva 소재 재판매 제한 등).",
               "Gumroad 등록 규정과 수수료는 판매 전에 공식 안내에서 확인하세요.",
               "유료 글꼴·유료 사진·유명 로고가 템플릿에 들어 있지 않은지 확인하세요."]


def draft(pack, counts):
    t = pack["theme"]
    title = f"{pack['pack_name']} — 편집 가능한 {t} 썸네일·채널아트 템플릿"
    desc = (f"{t} 채널을 위한 Canva 템플릿 묶음입니다. 썸네일 {counts.get('thumb', 0)}개, 채널아트 {counts.get('art', 0)}개. "
            f"링크를 눌러 바로 편집하세요. 유튜브·구글 공식 상품이 아닙니다.")
    tags = [f"{t} 썸네일", "유튜브 썸네일", "채널아트", "canva 템플릿", "크리에이터", "썸네일 템플릿"]
    return {"title": title, "description": desc, "tags": tags, "price_text": pack.get("price_text", ""), "checks": CANVA_CHECK}


def to_text(d):
    return "\n".join([f"제목: {d['title']}", f"설명: {d['description']}", "태그: " + ", ".join(d["tags"]),
                      f"가격 문구: {d['price_text']}", ""] + ["[확인] " + c for c in d["checks"]]) + "\n"
