import argparse, json, os, shutil
from PIL import Image
from . import prep, outbox


def main(argv=None):
    p = argparse.ArgumentParser(prog="printorder", description="주문 제작 인쇄 파일 점검·변환·제작사 전달함 (실제 제작사 연결 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    c = s.add_parser("check"); c.add_argument("image"); c.add_argument("--product", required=True); c.add_argument("--fit", default="cover", choices=["cover", "contain"])
    r = s.add_parser("prepare"); r.add_argument("image"); r.add_argument("out"); r.add_argument("--product", required=True); r.add_argument("--fit", default="cover", choices=["cover", "contain"])
    d = s.add_parser("dispatch"); d.add_argument("order_json"); d.add_argument("--outbox", default="outbox.json"); d.add_argument("--vendor-dir", default="vendor_inbox", help="시험용 가짜 제작사: 이 폴더에 파일을 복사")
    a = p.parse_args(argv)
    try:
        if a.cmd == "check":
            x = prep.check(Image.open(a.image), a.product, a.fit); print(f"{x['level']} · 약 {x['dpi']}dpi · 잘림 {x['crop'] * 100:.0f}%"); [print(" -", i) for i in x["issues"]]; return 0 if x["level"] != "reject" else 1
        if a.cmd == "prepare":
            im, x = prep.prepare(Image.open(a.image), a.product, a.fit); im.save(a.out, dpi=(prep.DPI, prep.DPI)); print(f"저장: {a.out} {im.size} {prep.DPI}dpi ({x['level']})"); return 0
        o = json.load(open(a.order_json, encoding="utf-8"))
        def fake_vendor(order):
            dst = os.path.join(a.vendor_dir, order["order_id"]); os.makedirs(dst, exist_ok=True)
            for f in order["files"]: shutil.copy(f, dst)
            json.dump(order, open(os.path.join(dst, "order.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print(outbox.dispatch(a.outbox, o, fake_vendor)); return 0
    except (prep.PrepError, outbox.OutboxError, OSError, ValueError) as e:
        print(f"[오류] {e}"); return 2
