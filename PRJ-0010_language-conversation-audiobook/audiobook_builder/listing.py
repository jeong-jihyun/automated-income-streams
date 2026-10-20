"""상품 설명·목차 초안 (복사해서 쓰는 용도)."""
from .audio import fmt


def draft(title, chapter_info, provider_name):
    total = sum(i["seconds"] for _, _, i in chapter_info)
    n = sum(len(r) for _, r, _ in chapter_info)
    lines = [f"제목: {title}",
             f"설명: 상황별 회화 {n}문장을 {len(chapter_info)}개 챕터(약 {fmt(total)})로 묶은 오디오북과 교재 PDF입니다. "
             "문장마다 따라 말할 수 있는 무음 간격이 들어 있습니다.", "", "목차:"]
    lines += [f" {i}. {name} ({len(rows)}문장)" for i, (name, rows, _) in enumerate(chapter_info, 1)]
    lines += ["", "[확인] 음성 제공자: " + provider_name]
    if provider_name == "silent":
        lines.append("[주의] silent 는 시험용 무음입니다. 판매하려면 직접 녹음 또는 약관이 명확한 음성을 쓰세요.")
    if provider_name == "edge-tts":
        lines.append("[주의] edge-tts 는 비공식 도구라 상업 이용·재판매 약관 위험이 있습니다. 판매 전 공식 약관을 확인하세요.")
    lines += ["[확인] 번역 정확성과 발음은 사람이 검수하세요.", "[확인] 다른 교재·강의의 문장을 그대로 옮기지 않았는지 확인하세요."]
    return "\n".join(lines) + "\n"
