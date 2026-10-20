"""라이선스 사용범위 표와 상품 설명 초안 (복사해서 쓰는 용도). 법률 문구는 초안이며 전문가 확인 필요."""

LICENSE_ROWS = [("개인 사용", "가능", "예시"), ("상업 사용(인쇄물·영상)", "가능", "예시"),
                ("웹/앱 임베딩", "별도 협의", "예시"), ("폰트 파일 재배포·재판매", "불가", "예시")]


def license_table():
    lines = ["# 라이선스 사용범위 (초안 — 공개 전 전문가 확인 필요)", "", "| 용도 | 허용 | 비고 |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in LICENSE_ROWS]
    return "\n".join(lines) + "\n"


def product_draft(family, glyph_count, required_count, sample):
    pct = glyph_count / required_count * 100 if required_count else 0
    return (f"# {family} 상품 설명 초안\n\n"
            f"- 글자 수: {glyph_count}자 (필수 목록 {required_count}자 중 {pct:.0f}%)\n"
            f"- 미리보기 문장: {sample}\n"
            "- 마켓별 최소 글자 수·심사 기준은 공식 안내를 확인하세요 (여기서는 미확인).\n"
            "- 다른 폰트의 글자 윤곽을 따라 그리거나 변환한 글자가 없는지 확인하세요.\n")
