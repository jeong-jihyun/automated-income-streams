"""하이퍼링크 플래너 PDF 생성기 (ReportLab)."""
import os
from datetime import date, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .config import PlannerConfig, THEMES
from .labels import LABELS
from .calendar_utils import (month_grid, weeks_of_year, days_of_year,
                             day_key, week_key, month_key)

W, H = 842, 595   # A4 가로 (pt)
TAB_W = 46        # 오른쪽 탭 폭
LEFT = 40

BUNDLED_FONT = os.path.join(os.path.dirname(__file__), "fonts", "NanumGothic.ttf")


def _font(cfg):
    """TTF를 PDF에 내장한다(보는 기기에 폰트가 없어도 한글이 보이도록)."""
    path = cfg.font_path if cfg.font_path and os.path.exists(cfg.font_path) else BUNDLED_FONT
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont("PlannerFont", path))
        return "PlannerFont"
    return "Helvetica"  # 영어 전용 대체 (한글 불가)


class Planner:
    def __init__(self, cfg: PlannerConfig, path):
        self.cfg = cfg.validate()
        self.L = LABELS[cfg.lang]
        self.th = {k: HexColor(v) for k, v in THEMES[cfg.theme].items()}
        self.font = _font(cfg)
        self.c = canvas.Canvas(path, pagesize=(W, H))
        self.c.setTitle(cfg.title or f"{cfg.year} {self.L['cover']}")
        self.links = []      # (페이지, 목적지 이름) 검증용
        self.dests = set()
        self.dest_page = {}
        self.pages = 0

    # ---- 공통 ----
    def _page_start(self, key, title):
        self.c.bookmarkPage(key)
        self.dests.add(key)
        self.pages += 1
        self.dest_page[key] = self.pages
        c = self.c
        c.setFillColor(self.th["main"]); c.rect(0, H-50, W, 50, stroke=0, fill=1)
        c.setFillColor(HexColor("#FFFFFF")); c.setFont(self.font, 20)
        c.drawString(LEFT, H-33, title)
        self._tabs(key)

    def _link(self, x, y, w, h, dest):
        self.c.linkRect("", dest, (x, y, x+w, y+h), relative=0, thickness=0)
        self.links.append((self.pages, dest))

    def _tabs(self, current):
        c = self.c
        items = [(self.L["year"], "year")] + \
                [(m, month_key(i+1)) for i, m in enumerate(self.L["months"])] + \
                [(self.L["notes"], "notes_1")]
        top, bottom = H-60, 20
        h = (top-bottom)/len(items)
        for i, (name, dest) in enumerate(items):
            y = top - (i+1)*h
            active = (dest == current) or (current.startswith("month_") and dest == current)
            c.setFillColor(self.th["main"] if active else self.th["sub"])
            c.rect(W-TAB_W, y+1, TAB_W-4, h-2, stroke=0, fill=1)
            c.setFillColor(HexColor("#FFFFFF") if active else self.th["text"])
            c.setFont(self.font, 9)
            c.drawCentredString(W-TAB_W/2-2, y+h/2-3, name)
            self._link(W-TAB_W, y, TAB_W, h, dest)

    # ---- 페이지들 ----
    def cover(self):
        c = self.c
        self._page_start("cover", "")
        c.setFillColor(self.th["sub"]); c.rect(0, 0, W, H-50, stroke=0, fill=1)
        c.setFillColor(self.th["main"]); c.setFont(self.font, 54)
        c.drawCentredString((W-TAB_W)/2, H/2+20, str(self.cfg.year))
        c.setFont(self.font, 26)
        c.drawCentredString((W-TAB_W)/2, H/2-30, self.cfg.title or self.L["cover"])
        c.showPage()

    def yearly(self):
        c = self.c
        self._page_start("year", f"{self.cfg.year} {self.L['year']}")
        cols, rows = 4, 3
        bw, bh = (W-TAB_W-LEFT*2)/cols, (H-110)/rows
        names = self.L["dow_mon"] if self.cfg.week_start == "monday" else self.L["dow_sun"]
        for m in range(1, 13):
            r, k = divmod(m-1, cols)
            x = LEFT + k*bw
            y = H-70 - (r+1)*bh
            c.setFillColor(self.th["main"]); c.setFont(self.font, 11)
            c.drawString(x+4, y+bh-14, self.L["months"][m-1])
            self._link(x, y+bh-20, bw-8, 20, month_key(m))
            c.setFont(self.font, 6); c.setFillColor(self.th["text"])
            cw = (bw-12)/7
            for i, n in enumerate(names):
                c.drawCentredString(x+4+cw*i+cw/2, y+bh-28, n)
            for wi, week in enumerate(month_grid(self.cfg.year, m, self.cfg.week_start)):
                for di, d in enumerate(week):
                    if d:
                        c.drawCentredString(x+4+cw*di+cw/2, y+bh-40-wi*11, str(d))
                        if self.cfg.include_daily:
                            self._link(x+4+cw*di, y+bh-43-wi*11, cw, 10,
                                       day_key(date(self.cfg.year, m, d)))
        c.showPage()

    def monthly(self, m):
        c = self.c
        key = month_key(m)
        self._page_start(key, f"{self.cfg.year} {self.L['months'][m-1]}")
        names = self.L["dow_mon"] if self.cfg.week_start == "monday" else self.L["dow_sun"]
        grid = month_grid(self.cfg.year, m, self.cfg.week_start)
        gw = W-TAB_W-LEFT*2
        cw = gw/7
        top = H-70
        rh = (top-30)/6
        for i, n in enumerate(names):
            c.setFillColor(self.th["sub"]); c.rect(LEFT+i*cw, top-18, cw, 18, stroke=0, fill=1)
            c.setFillColor(self.th["text"]); c.setFont(self.font, 10)
            c.drawCentredString(LEFT+i*cw+cw/2, top-13, n)
        c.setStrokeColor(self.th["main"]); c.setLineWidth(0.4)
        for r, week in enumerate(grid):
            for i, d in enumerate(week):
                x, y = LEFT+i*cw, top-18-(r+1)*rh
                c.rect(x, y, cw, rh, stroke=1, fill=0)
                if d:
                    c.setFillColor(self.th["main"]); c.setFont(self.font, 11)
                    c.drawString(x+5, y+rh-15, str(d))
                    if self.cfg.include_daily:
                        self._link(x, y, cw, rh, day_key(date(self.cfg.year, m, d)))
        c.showPage()

    def weekly(self, start):
        c = self.c
        end = start + timedelta(days=6)
        self._page_start(week_key(start), f"{self.L['weekly']} {start:%m/%d} - {end:%m/%d}")
        names = self.L["dow_mon"] if self.cfg.week_start == "monday" else self.L["dow_sun"]
        bw = (W-TAB_W-LEFT*2)/2
        bh = (H-100)/4
        c.setStrokeColor(self.th["main"]); c.setLineWidth(0.4)
        for i in range(7):
            d = start + timedelta(days=i)
            col, row = divmod(i, 4)
            x, y = LEFT+col*bw, H-70-(row+1)*bh
            c.rect(x, y, bw-6, bh-6, stroke=1, fill=0)
            c.setFillColor(self.th["main"]); c.setFont(self.font, 11)
            c.drawString(x+6, y+bh-22, f"{d:%m/%d} {names[i]}")
            if d.year == self.cfg.year and self.cfg.include_daily:
                self._link(x, y+bh-30, bw-6, 24, day_key(d))
        c.showPage()

    def daily(self, d):
        c = self.c
        names = self.L["dow_mon"]
        self._page_start(day_key(d), f"{d:%Y.%m.%d} ({names[d.weekday()]})")
        # 상위 이동 링크
        c.setFillColor(HexColor("#FFFFFF")); c.setFont(self.font, 10)
        c.drawRightString(W-TAB_W-LEFT, H-33, f"{self.L['months'][d.month-1]} ▸")
        self._link(W-TAB_W-LEFT-80, H-45, 80, 40, month_key(d.month))
        half = (W-TAB_W-LEFT*2)/2
        c.setStrokeColor(self.th["main"]); c.setLineWidth(0.4)
        for i, (label, x) in enumerate(((self.L["schedule"], LEFT), (self.L["todo"], LEFT+half))):
            c.setFillColor(self.th["main"]); c.setFont(self.font, 12)
            c.drawString(x+6, H-78, label)
            for j in range(14):
                y = H-95-j*30
                c.line(x+6, y, x+half-12, y)
        c.showPage()

    def notes(self, n):
        c = self.c
        self._page_start(f"notes_{n}", f"{self.L['notes']} {n}")
        c.setStrokeColor(self.th["sub"]); c.setLineWidth(0.3)
        x = LEFT
        for gx in range(int(LEFT), int(W-TAB_W-LEFT), 24):
            c.line(gx, 30, gx, H-65)
        for gy in range(30, H-65, 24):
            c.line(LEFT, gy, W-TAB_W-LEFT, gy)
        c.showPage()

    def build(self):
        cfg = self.cfg
        self.cover(); self.yearly()
        for m in range(1, 13): self.monthly(m)
        if cfg.include_weekly:
            for s in weeks_of_year(cfg.year, cfg.week_start): self.weekly(s)
        if cfg.include_daily:
            for d in days_of_year(cfg.year): self.daily(d)
        for n in range(1, max(cfg.note_pages, 1)+1): self.notes(n)
        self.c.save()
        return {"pages": self.pages, "links": len(self.links),
                "dests": self.dests, "dest_page": self.dest_page,
                "link_list": self.links}


def generate(cfg: PlannerConfig, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    return Planner(cfg, out_path).build()
