"""생성된 PDF의 링크를 pypdf로 다시 읽어 깨진 링크를 찾는다.
reportlab은 링크 목적지를 [페이지 객체, /Fit] 배열로 저장하므로 대상 페이지 번호를 직접 계산한다."""
import os
from pypdf import PdfReader


def link_targets(path):
    """[(출발 페이지, 도착 페이지 또는 None), ...] (1부터 시작)"""
    r = PdfReader(path)
    ref_to_no = {p.indirect_reference.idnum: i for i, p in enumerate(r.pages, start=1)}
    out = []
    for pi, page in enumerate(r.pages, start=1):
        for a in (page.get("/Annots") or []):
            a = a.get_object()
            if a.get("/Subtype") != "/Link":
                continue
            dest = a.get("/Dest")
            if dest is None and "/A" in a:
                dest = a["/A"].get_object().get("/D")
            tgt = None
            if isinstance(dest, list) and dest:
                ref = getattr(dest[0], "idnum", None)
                tgt = ref_to_no.get(ref)
            out.append((pi, tgt))
    return out


def validate_pdf(path, max_mb=60):
    targets = link_targets(path)
    n_pages = len(PdfReader(path).pages)
    broken = [(s, t) for s, t in targets if t is None or not 1 <= t <= n_pages]
    size_mb = os.path.getsize(path) / 1048576
    return {"pages": n_pages, "links": len(targets), "broken": broken,
            "size_mb": round(size_mb, 2), "size_ok": size_mb <= max_mb,
            "ok": bool(targets) and not broken and size_mb <= max_mb}
