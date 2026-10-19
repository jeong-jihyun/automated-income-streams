"""플랫폼별 상품 문구 초안. 최종 문구는 사람이 다듬는다."""


def make_copy(cfg, info):
    ko = cfg.lang == "ko"
    y = cfg.year
    if ko:
        title = f"{y} 굿노트 디지털 플래너 | 하이퍼링크 연간·월간{'·주간' if cfg.include_weekly else ''}{'·일간' if cfg.include_daily else ''}"
        desc = (f"{y}년 한 해를 계획하는 하이퍼링크 플래너 PDF입니다.\n"
                f"- 총 {info['pages']}페이지, 링크 {info['links']}개 (오른쪽 탭을 누르면 해당 월로 이동)\n"
                f"- 주 시작 요일: {'월요일' if cfg.week_start=='monday' else '일요일'}\n"
                "- 굿노트, 노타빌리티 등 PDF 주석 앱에서 사용하세요.\n"
                "- 디지털 상품이므로 다운로드 후 교환·환불이 어렵습니다.")
        tags = ["굿노트", "디지털플래너", f"{y}플래너", "아이패드다이어리", "하이퍼링크"]
    else:
        title = f"{y} Digital Planner for GoodNotes | Hyperlinked Monthly Weekly Daily"
        desc = (f"A hyperlinked {y} planner PDF.\n"
                f"- {info['pages']} pages, {info['links']} links (tap the side tabs to jump to a month)\n"
                f"- Week starts on {cfg.week_start.title()}\n"
                "- Works with GoodNotes, Notability and other PDF annotation apps.\n"
                "- Digital product: no physical item will be shipped.")
        tags = ["goodnotes planner", "digital planner", f"{y} planner", "ipad planner", "hyperlinked"]
    return {"title": title, "description": desc, "tags": tags}
