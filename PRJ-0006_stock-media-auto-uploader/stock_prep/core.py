"""스톡 업로드 준비 도구: 파일 검사, 키워드 정리, 사이트별 메타데이터 CSV, 체크리스트, 보고서.
외부 사이트 로그인·자동 업로드·외부 서비스 전송은 하지 않는다 (모두 로컬 처리)."""
import csv
import json
import os
import re

from PIL import Image, ImageFilter, ImageStat

HERE = os.path.dirname(__file__)
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp", ".gif"}


def load_settings(path=None):
    with open(path or os.path.join(HERE, "settings.json"), encoding="utf-8") as f:
        return json.load(f)


def list_images(folder):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"사진 폴더가 없습니다: {folder}")
    names = sorted(n for n in os.listdir(folder)
                   if os.path.isfile(os.path.join(folder, n)))
    return names


def blur_variance(img, max_side=1000):
    """라플라시안 분산. 작을수록 흐림. 큰 사진은 줄여서 계산한다."""
    g = img.convert("L")
    if max(g.size) > max_side:
        g.thumbnail((max_side, max_side))
    lap = g.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
    return ImageStat.Stat(lap).var[0]


def check_file(path, cfg):
    """한 파일을 검사해 {'ok':bool,'problems':[...],'info':{...}} 를 돌려준다."""
    c = cfg["check"]
    problems, info = [], {}
    size_mb = os.path.getsize(path) / 1024 / 1024
    info["size_mb"] = round(size_mb, 2)
    if os.path.splitext(path)[1].lower() not in IMG_EXT:
        return {"ok": False, "problems": ["이미지 파일이 아닙니다"], "info": info}
    try:
        with Image.open(path) as im:
            im.load()
            fmt = im.format
            w, h = im.size
            info.update(format=fmt, width=w, height=h, megapixels=round(w * h / 1e6, 2))
            if fmt not in c["allowed_formats"]:
                problems.append(f"형식 {fmt} 은(는) 허용 목록 {c['allowed_formats']} 에 없습니다")
            if w * h / 1e6 < c["min_megapixels"]:
                problems.append(f"해상도 {w*h/1e6:.1f}MP 가 최소 {c['min_megapixels']}MP 보다 작습니다")
            var = blur_variance(im, c["blur_analysis_max_side"])
            info["sharpness"] = round(var, 1)
            if var < c["blur_min_variance"]:
                problems.append(f"흐릴 수 있습니다 (선명도 {var:.1f} < {c['blur_min_variance']})")
    except Exception as e:  # 깨진 파일 등
        return {"ok": False, "problems": [f"이미지를 열 수 없습니다: {type(e).__name__}"], "info": info}
    if size_mb > c["max_file_mb"]:
        problems.append(f"용량 {size_mb:.1f}MB 가 최대 {c['max_file_mb']}MB 를 넘습니다")
    return {"ok": not problems, "problems": problems, "info": info}


def read_memo(csv_path):
    """메모 CSV (열: file, memo 필수 / title 선택). 없거나 형식이 틀리면 오류."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"메모 CSV가 없습니다: {csv_path}")
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        if not rd.fieldnames or "file" not in rd.fieldnames or "memo" not in rd.fieldnames:
            raise ValueError("메모 CSV에는 file, memo 열이 필요합니다 (title 열은 선택).")
        return {r["file"].strip(): {k: (v or "").strip() for k, v in r.items()} for r in rd if r.get("file")}


def clean_keywords(memo, cfg):
    """메모를 키워드 목록으로 정리. 중복·금지어 제거, 개수 제한. (키워드, 경고) 반환."""
    kw_cfg = cfg["keywords"]
    banned = {b.lower() for b in kw_cfg["banned"]}
    persons = {p.lower() for p in kw_cfg["person_words"]}
    warnings, out, seen = [], [], set()
    for tok in re.split(r"[,\n;/]+|\s{2,}", memo):
        for word in ([tok.strip()] if " " in tok.strip() and tok.strip().lower() in banned else tok.split()):
            w = word.strip().lower()
            if not w:
                continue
            if w in banned:
                warnings.append(f"상표·브랜드 단어 제거: {w}")
                continue
            if w in seen:
                continue
            seen.add(w)
            if w in persons:
                warnings.append(f"사람 관련 단어 '{w}': 모델 릴리스 확인 필요")
            out.append(w)
    if len(out) > kw_cfg["max_count"]:
        warnings.append(f"키워드 {len(out)}개 → {kw_cfg['max_count']}개로 줄임 (무관한 단어는 심사 불이익)")
        out = out[:kw_cfg["max_count"]]
    return out, warnings


def draft_title(memo_row, keywords):
    if memo_row.get("title"):
        return memo_row["title"]
    return " ".join(w.capitalize() for w in keywords[:5]) or ""


CHECKLIST = [
    "사람 얼굴이 알아볼 수 있게 나오나요? → 모델 릴리스 필요",
    "상표·로고·제품 디자인이 보이나요? → 제거하거나 편집용(Editorial) 여부 확인",
    "건물 내부, 사유지, 예술작품이 나오나요? → 재산 릴리스 필요",
    "AI로 만든 이미지인가요? → 사이트별 허용 여부·표시 의무를 공식 안내에서 확인",
    "제목·키워드가 사진 내용과 실제로 맞나요?",
]


def prepare(folder, memo_csv, out_dir, settings_path=None):
    """폴더 전체를 검사하고 사이트별 CSV·체크리스트·보고서를 만든다."""
    cfg = load_settings(settings_path)
    names = list_images(folder)
    if not names:
        raise ValueError("사진 폴더가 비어 있습니다.")
    memo = read_memo(memo_csv)
    os.makedirs(out_dir, exist_ok=True)
    rows, passed, failed, no_memo = [], [], [], []
    for n in names:
        res = check_file(os.path.join(folder, n), cfg)
        m = memo.get(n)
        if m is None and res["ok"]:
            no_memo.append(n)
        if res["ok"] and m is not None:
            kws, warns = clean_keywords(m["memo"], cfg)
            rows.append({"file": n, "title": draft_title(m, kws), "keywords": kws, "warns": warns,
                         "info": res["info"]})
            passed.append(n)
        elif not res["ok"]:
            failed.append((n, res["problems"]))
    for site, sc in cfg["sites"].items():
        with open(os.path.join(out_dir, f"metadata_{site}.csv"), "w", encoding="utf-8-sig", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(sc["columns"])
            for r in rows:
                vals = {"Filename": r["file"], "파일명": r["file"], "Title": r["title"], "제목": r["title"],
                        "설명": r["title"], "Keywords": ",".join(r["keywords"]), "키워드": ",".join(r["keywords"])}
                wr.writerow([vals.get(c, "") for c in sc["columns"]])
    with open(os.path.join(out_dir, "release_checklist.md"), "w", encoding="utf-8") as f:
        f.write("# 초상권·재산권 체크리스트 (파일마다 사람이 확인)\n\n")
        for r in rows:
            f.write(f"## {r['file']}\n")
            for q in CHECKLIST:
                f.write(f"- [ ] {q}\n")
            for w in r["warns"]:
                f.write(f"- ⚠ {w}\n")
            f.write("\n")
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(f"# 업로드 준비 보고서\n\n- 전체 파일: {len(names)}개\n- 준비 완료: {len(passed)}개\n- 문제 있음: {len(failed)}개\n"
                f"- 메모가 없어 제외: {len(no_memo)}개\n\n")
        f.write("> 규격 숫자는 예시값입니다. 실제 업로드와 제출은 사람이 사이트에서 직접 합니다.\n\n")
        for n, ps in failed:
            f.write(f"## 문제: {n}\n" + "".join(f"- {p}\n" for p in ps) + "\n")
        for n in no_memo:
            f.write(f"- 메모 없음: {n}\n")
    return {"total": len(names), "passed": passed, "failed": failed, "no_memo": no_memo}
