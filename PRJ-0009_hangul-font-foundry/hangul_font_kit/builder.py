"""SVG 글리프 → TTF. (OTF/CFF 는 만들지 않음)"""
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from .svgread import read_svg


def _glyph(subpaths, cfg):
    base = cfg["baseline_y"]
    tt = TTGlyphPen(None)
    pen = Cu2QuPen(tt, max_err=1.0)
    f = lambda x, y: (round(x), round(base - y))  # SVG 는 아래로 갈수록 y 증가
    for s in subpaths:
        for seg in s["segs"]:
            k, v = seg[0], seg[1:]
            pts = [f(v[i], v[i + 1]) for i in range(0, len(v), 2)]
            if k == "M": pen.moveTo(pts[0])
            elif k == "L": pen.lineTo(pts[0])
            elif k == "C": pen.curveTo(*pts)
            elif k == "Q": pen.qCurveTo(*pts)
        pen.closePath()
    return tt.glyph()


def advance_for(cp, cfg):
    if cp == 0x20:
        return cfg["advance_space"]
    if 0xAC00 <= cp <= 0xD7A3:
        return cfg["advance_hangul"]
    return cfg["advance_other"]


def build_ttf(found, cfg, out_path):
    """found: {codepoint: svg 경로}. 읽은 글자 수를 돌려준다."""
    if not found:
        raise ValueError("만들 글자가 없습니다")
    order = [".notdef"] + [f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:X}" for cp in sorted(found)]
    cmap = {cp: (f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:X}") for cp in found}
    fb = FontBuilder(cfg["units_per_em"], isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (cfg["advance_hangul"], 0)}
    for cp, path in found.items():
        name = cmap[cp]
        g = read_svg(path)
        glyphs[name] = _glyph(g["subpaths"], cfg)
        metrics[name] = (advance_for(cp, cfg), 0)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=cfg["ascent"], descent=cfg["descent"])
    fam, sty = cfg["family_name"], cfg["style_name"]
    fb.setupNameTable({"familyName": fam, "styleName": sty, "uniqueFontIdentifier": f"{fam}-{sty}-{cfg['version']}",
                       "fullName": f"{fam} {sty}", "psName": f"{fam}-{sty}", "version": f"Version {cfg['version']}"})
    fb.setupOS2(sTypoAscender=cfg["ascent"], sTypoDescender=cfg["descent"], usWinAscent=cfg["ascent"],
                usWinDescent=abs(cfg["descent"]))
    fb.setupPost()
    fb.save(out_path)
    return len(found)
