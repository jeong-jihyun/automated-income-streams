"""상품 등록용 미리보기 이미지: PDF 페이지를 PNG로 변환 (pdftoppm 필요)."""
import subprocess, os, shutil


def make_previews(pdf, out_dir, pages=(1, 2, 3, 15), dpi=60):
    if not shutil.which("pdftoppm"):
        return []
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for p in pages:
        prefix = os.path.join(out_dir, f"preview_{p:03d}")
        r = subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(p), "-l", str(p),
                            "-singlefile", pdf, prefix], capture_output=True)
        if r.returncode == 0 and os.path.exists(prefix + ".png"):
            made.append(prefix + ".png")
    return made
