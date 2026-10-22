import csv
import io

RECEIPT_COLS = ["date", "store", "item", "qty", "amount", "total", "vat"]
CARD_COLS = ["name", "company", "mobile", "tel", "email", "address"]


def _safe(v):
    """엑셀에서 수식으로 실행되지 않도록 = + - @ 로 시작하는 글자 앞에 작은따옴표를 붙인다."""
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "@") or (s[:1] == "-" and not s[1:2].isdigit()) else s


def receipts_csv(parsed_list):
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(RECEIPT_COLS)
    for r in parsed_list:
        rows = r["items"] or [{"name": "", "qty": "", "amount": ""}]
        for it in rows:
            w.writerow([_safe(x) for x in (r["date"], r["store"], it["name"], it["qty"], it["amount"], r["total"], r["vat"])])
    return buf.getvalue()


def cards_csv(parsed_list):
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(CARD_COLS)
    for c in parsed_list:
        w.writerow([_safe(c[k]) for k in CARD_COLS])
    return buf.getvalue()
