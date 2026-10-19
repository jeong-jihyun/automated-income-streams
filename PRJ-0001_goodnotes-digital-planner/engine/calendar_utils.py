"""날짜 계산: 달력 주 배열, 주 목록."""
import calendar
from datetime import date, timedelta


def month_grid(year, month, week_start):
    """해당 월의 주별 날짜 리스트(없는 칸은 None)."""
    first = 0 if week_start == "monday" else 6  # calendar.MONDAY=0, SUNDAY=6
    cal = calendar.Calendar(firstweekday=first)
    return [[d if d != 0 else None for d in w] for w in cal.monthdayscalendar(year, month)]


def weeks_of_year(year, week_start):
    """해당 연도 1/1이 포함된 주부터 12/31이 포함된 주까지 (시작일 리스트)."""
    d = date(year, 1, 1)
    back = d.weekday() if week_start == "monday" else (d.weekday() + 1) % 7
    d = d - timedelta(days=back)
    end = date(year, 12, 31)
    out = []
    while d <= end:
        out.append(d)
        d += timedelta(days=7)
    return out


def days_of_year(year):
    d = date(year, 1, 1)
    while d.year == year:
        yield d
        d += timedelta(days=1)


def day_key(d): return f"day_{d.isoformat()}"
def week_key(start): return f"week_{start.isoformat()}"
def month_key(m): return f"month_{m:02d}"
