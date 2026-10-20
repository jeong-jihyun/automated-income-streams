"""제목·설명·키워드 초안 (복사해서 쓰는 용도). 자동 등록은 하지 않는다."""

AI_NOTICE = ("KDP 업로드 화면에서 'AI 생성 콘텐츠 여부'를 사람이 직접, 정확히 선택해야 합니다. "
             "현재 정책은 올릴 때 KDP 공식 도움말로 다시 확인하세요.")


def draft(theme, page_count, specs, audience="어린이와 어른"):
    kws = [f"{theme} 색칠 공부", f"{theme} 컬러링북", "coloring book", "색칠공부 책", "스트레스 해소",
           "취미 색칠", f"{theme} 그림"][: specs["metadata_keywords_max"]]
    title = f"{theme} 컬러링북 — {audience}를 위한 편안한 색칠 공부"
    desc = (f"{theme}를 주제로 한 {page_count}쪽 흑백 선화 색칠 공부 책입니다. "
            f"한 면에 그림 한 장, 뒷면은 비워 두어 번짐 걱정 없이 색칠할 수 있습니다.")
    return {"title": title, "description": desc, "keywords": kws,
            "ai_notice": AI_NOTICE,
            "caution": ["유명 캐릭터·브랜드를 닮은 그림은 쓰지 않았는지 확인하세요.",
                        "내용이 거의 같은 책을 대량으로 내면 저품질로 제한될 수 있으니 주제·구성에 변화를 주세요."]}


def to_text(d):
    lines = [f"제목: {d['title']}", f"설명: {d['description']}", "키워드: " + ", ".join(d["keywords"]), "",
             "[AI 사용 안내] " + d["ai_notice"], ""] + ["[주의] " + c for c in d["caution"]]
    return "\n".join(lines) + "\n"
