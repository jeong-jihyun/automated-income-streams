"""사진 점검(너무 어둡거나 흐리면 다시 찍기 안내)과 음식 인식 연결부. 인식기는 classifier(path)->[(라벨, 확신도)] 함수를 꽂아 쓴다."""
import os
from PIL import Image, ImageFilter, ImageStat


def check_photo(path):
    if not os.path.isfile(path): raise FileNotFoundError(path)
    try:
        im = Image.open(path); im.load()
    except Exception:
        return {"ok": False, "problems": ["사진으로 읽을 수 없어요"]}
    g = im.convert("L"); probs = []
    if min(im.size) < 224: probs.append("사진이 너무 작아요(짧은 변 224px 이상)")
    if ImageStat.Stat(g).mean[0] < 40: probs.append("너무 어두워요")
    if ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0] < 20: probs.append("흐리거나 단조로워요")
    return {"ok": not probs, "problems": probs}


def recognize(path, classifier, min_conf=0.3):
    """인식 결과 중 확신도가 너무 낮은 것은 버린다. 인식기 오류·빈 결과는 빈 목록(→ 직접 입력 안내)."""
    c = check_photo(path)
    if not c["ok"]: return {"items": [], "problems": c["problems"]}
    try:
        got = classifier(path) or []
    except Exception:
        return {"items": [], "problems": ["음식 인식에 실패했어요. 직접 입력해 주세요"]}
    return {"items": [(l, "M", float(cf)) for l, cf in got if cf >= min_conf], "problems": []}
