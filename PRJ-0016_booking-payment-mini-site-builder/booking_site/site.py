"""휴대폰 화면용 소개 페이지(정적 HTML)."""
import html


def build_page(cfg):
    e = html.escape
    svc = "".join(f"<li>{e(s['name'])} — {s['price']:,}원</li>" for s in cfg["services"])
    pol = "".join(f"<li>예약 {p['hours_before']}시간 전까지 취소: {p['percent']}% 환불</li>" for p in sorted(cfg["refund_policy"], key=lambda p: -p["hours_before"]))
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(cfg['shop_name'])}</title>
<style>body{{font-family:sans-serif;margin:0;padding:16px;max-width:480px;margin:auto;line-height:1.6}}button{{width:100%;padding:14px;font-size:16px}}</style></head>
<body><h1>{e(cfg['shop_name'])}</h1><p>영업시간 {e(cfg['open'])}~{e(cfg['close'])}</p>
<h2>서비스</h2><ul>{svc}</ul><h2>취소·환불 안내</h2><ul>{pol}</ul>
<p><small>※ 결제는 시험용입니다. 실제 결제가 되지 않습니다.</small></p>
<a href="/book"><button>예약하기</button></a></body></html>"""
