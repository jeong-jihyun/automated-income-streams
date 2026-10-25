import csv, os
from PIL import Image
from .process import process, PhotoError

EXT = (".jpg", ".jpeg", ".png")


def run(src, dst, preset="square_1000", color=(255, 255, 255), dry_run=False):
    if not os.path.isdir(src): raise PhotoError(f"입력 폴더가 없어요: {src}")
    files = sorted(f for f in os.listdir(src) if f.lower().endswith(EXT))
    rows = []
    if not dry_run: os.makedirs(dst, exist_ok=True)
    for f in files:
        try:
            im = Image.open(os.path.join(src, f)); im.load()
            out, info = process(im, preset, color)
            if not dry_run: out.save(os.path.join(dst, os.path.splitext(f)[0] + ".jpg"), quality=92)
            rows.append({"file": f, "status": "ok", "reason": ""})
        except PhotoError as e:
            rows.append({"file": f, "status": "fail", "reason": str(e)})
        except Exception as e:
            rows.append({"file": f, "status": "fail", "reason": f"파일을 열 수 없어요: {type(e).__name__}"})
    if not dry_run and rows:
        with open(os.path.join(dst, "report.csv"), "w", newline="", encoding="utf-8-sig") as fp:
            w = csv.DictWriter(fp, fieldnames=["file", "status", "reason"]); w.writeheader(); w.writerows(rows)
    return rows
