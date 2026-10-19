"""규격 검사 · 크기 맞춤 · 파일명 정리 · 제안 문구 초안."""
import json, os
from pathlib import Path
from PIL import Image, UnidentifiedImageError

IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def load_preset(name, path=None):
    p = Path(path) if path else Path(__file__).with_name("presets.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    if name not in data or name.startswith("_"):
        raise KeyError(f"프리셋 '{name}'이 없습니다. 가능한 이름: {[k for k in data if not k.startswith('_')]}")
    return data[name]


def list_images(folder):
    f = Path(folder)
    if not f.is_dir():
        raise NotADirectoryError(f"폴더가 아닙니다: {folder}")
    return sorted(p for p in f.iterdir() if p.suffix.lower() in IMG_EXT)


def has_transparency(img):
    if img.mode in ("RGBA", "LA"):
        return img.getchannel("A").getextrema()[0] < 255
    return "transparency" in img.info


def check_file(path, rule):
    """한 장 검사. 문제 목록(문자열 리스트)을 돌려준다. 비어 있으면 통과."""
    problems = []
    try:
        with Image.open(path) as img:
            img.load()
            if img.format not in rule["formats"]:
                problems.append(f"형식 {img.format} (필요: {'/'.join(rule['formats'])})")
            if img.size != (rule["width"], rule["height"]):
                problems.append(f"크기 {img.size[0]}x{img.size[1]} (필요: {rule['width']}x{rule['height']})")
            if rule.get("need_transparent") and not has_transparency(img):
                problems.append("투명 배경이 없음")
    except (UnidentifiedImageError, OSError):
        return ["이미지로 열 수 없는 파일"]
    kb = os.path.getsize(path) / 1024
    if kb > rule["max_kb"]:
        problems.append(f"용량 {kb:.0f}KB (최대 {rule['max_kb']}KB)")
    return problems


def check_folder(folder, rule):
    imgs = list_images(folder)
    results = {p.name: check_file(p, rule) for p in imgs}
    count_problem = None
    if len(imgs) != rule["count"]:
        count_problem = f"개수 {len(imgs)}개 (필요: {rule['count']}개)"
    ok = count_problem is None and all(not v for v in results.values())
    return {"ok": ok, "count": len(imgs), "count_problem": count_problem, "files": results}


def format_report(res):
    lines = ["# 이모티콘 규격 검수 보고서", ""]
    lines.append("결과: " + ("통과" if res["ok"] else "수정 필요"))
    if res["count_problem"]:
        lines.append(f"- {res['count_problem']}")
    for name, probs in res["files"].items():
        lines.append(f"- {'OK ' if not probs else 'FAIL'} {name}" + ("" if not probs else ": " + "; ".join(probs)))
    lines += ["", "※ 이 보고서는 파일 규격만 확인합니다. 실제 카카오 심사 통과 여부는 알 수 없으니 공식 안내를 꼭 확인하세요."]
    return "\n".join(lines)


def resize_all(folder, out_dir, rule):
    """비율을 유지하며 줄이고 투명 캔버스 중앙에 놓아 규격 크기로 맞춘다. 원본은 건드리지 않는다."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    done = []
    for p in list_images(folder):
        try:
            with Image.open(p) as im:
                im = im.convert("RGBA")
                im.thumbnail((rule["width"], rule["height"]), Image.LANCZOS)
                canvas = Image.new("RGBA", (rule["width"], rule["height"]), (0, 0, 0, 0))
                canvas.paste(im, ((rule["width"] - im.width) // 2, (rule["height"] - im.height) // 2), im)
                dest = out / (p.stem + ".png")
                canvas.save(dest, "PNG", optimize=True)
                done.append(dest.name)
        except (UnidentifiedImageError, OSError):
            continue
    return done


def rename_files(folder, prefix="emoticon", dry_run=False):
    """01 형식의 순번 이름(prefix_01.png)으로 복사 규칙을 만든다. 실제 변경은 dry_run=False일 때만."""
    imgs = list_images(folder)
    width = max(2, len(str(len(imgs))))
    plan = []
    for i, p in enumerate(imgs, 1):
        plan.append((p.name, f"{prefix}_{i:0{width}d}{p.suffix.lower()}"))
    if not dry_run:
        tmp = []
        for old, new in plan:  # 이름 충돌 방지: 임시 이름을 거친다
            t = Path(folder) / (".tmp_" + new)
            (Path(folder) / old).rename(t)
            tmp.append((t, Path(folder) / new))
        for t, n in tmp:
            t.rename(n)
    return plan


def make_plan_table(count=32, emotions=None):
    """구성표(목록) 틀을 CSV 문자열로 만든다."""
    emotions = emotions or ["인사", "기쁨", "슬픔", "화남", "놀람", "사랑", "피곤", "응원", "감사", "미안", "OK", "NO"]
    rows = ["번호,감정/상황,대사,메모"]
    for i in range(1, count + 1):
        rows.append(f"{i},{emotions[(i-1) % len(emotions)]},,")
    return "\n".join(rows)


def proposal_draft(name, concept, personality, count=32):
    return (f"[캐릭터 이름] {name}\n[한 줄 소개] {concept}\n[성격] {personality}\n"
            f"[구성] 총 {count}개, 일상 대화에서 자주 쓰는 감정·상황 중심\n"
            "[사용 장면] 친구/가족/직장 메신저 대화\n"
            "[주의] 직접 그린 그림만 사용했고 다른 캐릭터와 비슷하지 않은지 확인했습니다. (제출 전 본인 확인 필수)\n")
