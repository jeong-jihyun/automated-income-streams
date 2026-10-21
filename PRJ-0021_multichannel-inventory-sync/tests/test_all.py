import os
import threading
import pytest
from inventory_sync import core
from inventory_sync.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
CFG = core.load_config(os.path.join(S, "config.json"))


class Rec:
    def __init__(self, fail=()): self.calls, self.fail = [], set(fail)
    def __call__(self, ch, sku, qty):
        if ch in self.fail: raise ConnectionError("down")
        self.calls.append((ch, sku, qty))


@pytest.fixture
def db():
    d = core.connect(); core.import_csv(d, os.path.join(S, "stock.csv")); return d


def stock(db, sku): return db.execute("SELECT stock FROM items WHERE sku=?", (sku,)).fetchone()[0]


def test_sale_updates_master_and_all_channels(db):
    p = Rec(); r = core.sale(db, CFG, "e1", "naver", "A-100", 2, p)
    assert r["status"] == "ok" and stock(db, "A-100") == 8
    assert sorted(p.calls) == [("coupang", "A-100", 7), ("kakao", "A-100", 7), ("naver", "A-100", 7)]   # 안전재고 1 차감


def test_duplicate_event_ignored(db):
    p = Rec(); core.sale(db, CFG, "e1", "naver", "A-100", 2, p)
    assert core.sale(db, CFG, "e1", "naver", "A-100", 2, p)["status"] == "duplicate" and stock(db, "A-100") == 8


def test_oversell_rejected_without_negative_stock(db):
    p = Rec(); r = core.sale(db, CFG, "e1", "coupang", "A-200", 4, p)
    assert r["status"] == "oversold" and stock(db, "A-200") == 3
    assert core.sale(db, CFG, "e2", "coupang", "A-200", 3, p)["status"] == "ok" and stock(db, "A-200") == 0
    assert core.sellable(0, 1) == 0 and all(q == 0 for _, _, q in p.calls[-3:])   # 품절은 0으로 전파


def test_unchanged_qty_not_resent(db):
    p = Rec(); core.sync_sku(db, CFG, "A-100", p); n = len(p.calls)
    core.sync_sku(db, CFG, "A-100", p); assert len(p.calls) == n


def test_failed_channel_logged_and_retried(db):
    bad = Rec(fail={"kakao"}); r = core.sale(db, CFG, "e1", "naver", "A-100", 1, bad)
    assert r["sync"]["failed"] == ["kakao"] and len(bad.calls) == 2
    assert "kakao 전송 실패" in db.execute("SELECT msg FROM log").fetchone()[0]
    good = Rec(); core.sync_sku(db, CFG, "A-100", good)
    assert good.calls == [("kakao", "A-100", 8)]                      # 실패했던 채널만 다시 보냄


def test_validation(db):
    p = Rec()
    for args, msg in [(("e", "shopee", "A-100", 1), "모르는 채널"), (("e", "naver", "A-100", 0), "1 이상"), (("e", "naver", "ZZ", 1), "없는 sku")]:
        with pytest.raises(core.SyncError, match=msg): core.sale(db, CFG, *args, p)


def test_concurrent_sales_never_oversell(tmp_path):
    path = str(tmp_path / "c.db"); d = core.connect(path)
    core.import_csv(d, os.path.join(S, "stock.csv")); d.close()
    out = []
    def go(i):
        c = core.connect(path)
        try: out.append(core.sale(c, CFG, f"e{i}", "naver", "A-100", 1, Rec())["status"])
        finally: c.close()
    ts = [threading.Thread(target=go, args=(i,)) for i in range(15)]
    [t.start() for t in ts]; [t.join() for t in ts]
    chk = core.connect(path)
    assert out.count("ok") == 10 and out.count("oversold") == 5 and stock(chk, "A-100") == 0


def test_reconcile(db):
    core.sale(db, CFG, "e1", "naver", "A-100", 2, Rec())
    assert core.reconcile(db, CFG, {"naver": {"A-100": 7}, "kakao": {"A-100": 9}}) == [{"sku": "A-100", "channel": "kakao", "expected": 7, "actual": 9}]


def test_csv_and_config_errors(tmp_path):
    d = core.connect()
    for text, msg in [("sku,name\nA,x\n", "sku,name,stock"), ("sku,name,stock\nA,x,abc\n", "정수"), ("sku,name,stock\nA,x,-1\n", "음수"),
                      ("sku,name,stock\nA,x,1\nA,y,2\n", "중복")]:
        f = tmp_path / "s.csv"; f.write_text(text, encoding="utf-8")
        with pytest.raises(core.SyncError, match=msg): core.import_csv(d, str(f))
    for c in ('{"channels": []}', '{"channels": ["a","a"]}', '{"channels": ["a"], "safety_buffer": -1}'):
        f = tmp_path / "c.json"; f.write_text(c); 
        with pytest.raises(core.SyncError): core.load_config(str(f))


def test_cli(tmp_path, capsys):
    db = str(tmp_path / "i.db"); cfg = os.path.join(S, "config.json")
    assert main(["--db", db, "--config", cfg, "import", "--csv", os.path.join(S, "stock.csv")]) == 0
    assert main(["--db", db, "--config", cfg, "sale", "e1", "naver", "A-100", "2"]) == 0
    assert main(["--db", db, "--config", cfg, "show"]) == 0 and "기준 재고 8 / 판매가능 7" in capsys.readouterr().out
    assert main(["--db", db, "--config", cfg, "sale", "e2", "x", "A-100", "1"]) == 2
