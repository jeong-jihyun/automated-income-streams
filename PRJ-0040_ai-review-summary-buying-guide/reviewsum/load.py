"""리뷰 CSV 읽기: 열 이름은 rating(1~5), text, date(YYYY-MM-DD, 선택). 잘못된 줄은 건너뛰고 알려 준다."""
import csv
import datetime


class ReviewError(ValueError):
    pass


def load(path):
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        raise ReviewError(str(e))
    with f:
        rd = csv.reader(f); header = next(rd, None)
        if not header or "rating" not in header or "text" not in header: raise ReviewError("CSV에 rating, text 열이 필요합니다")
        ci = {h: i for i, h in enumerate(header)}; rows, skipped = [], []
        for n, r in enumerate(rd, 2):
            try:
                rating = int(r[ci["rating"]]); text = r[ci["text"]].strip()
                if not 1 <= rating <= 5 or not text: raise ValueError
                date = r[ci["date"]].strip() if "date" in ci and len(r) > ci["date"] else ""
                if date: datetime.date.fromisoformat(date)
                rows.append({"rating": rating, "text": text, "date": date})
            except (ValueError, IndexError):
                skipped.append(n)
    if not rows: raise ReviewError("읽을 수 있는 리뷰가 없습니다")
    return rows, skipped
