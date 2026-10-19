"""플랫폼별 상품 문구 초안 (최종 문구는 사람이 다듬는다)."""
from .presets import PRESETS
from .builder import TITLES


def make_listing(kind, job):
    label = PRESETS["jobs"][job]["label"]["ko"]
    name = TITLES[kind]
    return {
        "title": f"{name} 구글 시트 템플릿 | {label}용 자동 계산 수식 포함",
        "description": (f"{label}를 위한 {name} 구글 시트 템플릿입니다.\n"
                        "- 입력만 하면 합계·현황이 자동 계산됩니다.\n"
                        "- 구글 계정만 있으면 [사본 만들기]로 바로 사용할 수 있습니다.\n"
                        "- 사용설명서 시트가 포함되어 있습니다.\n"
                        "- 디지털 상품이므로 구매 후 교환·환불이 어렵습니다."),
        "tags": ["구글시트", "템플릿", name.replace(" ", ""), label, "엑셀", "자동계산"],
        "platform_note": "Gumroad/Etsy에는 원본 공유 링크가 아니라 '사본 만들기(/copy)' 링크를 전달하세요.",
    }
