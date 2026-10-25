import pytest
from petlog import advice, report, store
from petlog.cli import main


@pytest.fixture
def d():
    x = {"pets": {}}; store.add_pet(x, "콩이", "dog"); return x


def test_store_validation(d):
    with pytest.raises(store.PetError, match="종류"): store.add_pet(d, "a", "bird")
    with pytest.raises(store.PetError, match="이미"): store.add_pet(d, "콩이", "dog")
    with pytest.raises(store.PetError, match="날짜"): store.add_entry(d, "콩이", "2026-13-01")
    with pytest.raises(store.PetError, match="몸무게"): store.add_entry(d, "콩이", "2026-10-01", 500)
    with pytest.raises(store.PetError, match="없는"): store.add_entry(d, "없음", "2026-10-01")
    store.add_entry(d, "콩이", "2026-10-03"); store.add_entry(d, "콩이", "2026-10-01")
    assert [e["date"] for e in d["pets"]["콩이"]["entries"]] == ["2026-10-01", "2026-10-03"]


def test_urgent_signs_detected(d):
    store.add_entry(d, "콩이", "2026-10-24", symptoms=["호흡곤란"], note="초콜릿을 먹은 것 같아요")
    r = advice.advise(d["pets"]["콩이"], "2026-10-24")
    assert len(r["urgent"]) == 2 and "동물병원" in r["text"] and "진단이 아닙니다" in r["text"]


def test_old_urgent_entry_not_repeated(d):
    store.add_entry(d, "콩이", "2026-10-10", symptoms=["경련"])
    assert advice.advise(d["pets"]["콩이"], "2026-10-24")["urgent"] == []


def test_weight_trend_flag(d):
    store.add_entry(d, "콩이", "2026-10-01", 10.0); store.add_entry(d, "콩이", "2026-10-20", 8.8)
    w = advice.advise(d["pets"]["콩이"], "2026-10-20")["weight"]
    assert w["change_pct"] == -12.0 and w["flag"]
    store.add_entry(d, "콩이", "2026-10-21", 8.9); assert not advice.weight_trend(d["pets"]["콩이"]["entries"][-2:])["flag"]
    assert advice.weight_trend(d["pets"]["콩이"]["entries"][:1]) is None


def test_repeated_symptoms_window(d):
    for day in (20, 21, 22): store.add_entry(d, "콩이", f"2026-10-{day}", symptoms=["구토"])
    store.add_entry(d, "콩이", "2026-09-01", symptoms=["구토"])
    r = advice.advise(d["pets"]["콩이"], "2026-10-22"); assert r["watch"] == ["최근 7일 '구토' 기록 3회"]
    assert advice.advise(d["pets"]["콩이"], "2026-11-30")["watch"] == []


def test_no_medication_advice_text(d):
    store.add_entry(d, "콩이", "2026-10-22", symptoms=["구토"])
    t = advice.advise(d["pets"]["콩이"], "2026-10-22")["text"]
    assert "mg" not in t and "먹이세요" not in t


def test_report_table_escapes_pipe(d):
    store.add_entry(d, "콩이", "2026-10-22", 9.5, ["기침"], "밤에|심함")
    md = report.vet_summary("콩이", d["pets"]["콩이"], "2026-10-23"); assert "밤에/심함" in md and "| 2026-10-22 | 9.5 |" in md
    assert "(기록 없음)" in report.vet_summary("콩이", d["pets"]["콩이"], "2027-01-01")


def test_cli_and_atomic_file(tmp_path, capsys):
    f = str(tmp_path / "p.json")
    assert main(["--file", f, "add-pet", "나비", "cat"]) == 0
    assert main(["--file", f, "log", "나비", "--date", "2026-10-24", "--weight", "4.2", "--symptom", "소변 못 봄"]) == 0 and "응급" in capsys.readouterr().out
    assert main(["--file", f, "advise", "나비", "--today", "2026-10-24"]) == 0 and "🚨" in capsys.readouterr().out
    assert main(["--file", f, "report", "없음"]) == 2
    open(f, "w").write("{"); assert main(["--file", f, "advise", "나비"]) == 2
