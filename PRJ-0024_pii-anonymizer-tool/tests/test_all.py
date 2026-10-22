import csv
import io
import os
import pytest
from pii_tool import detect, mask
from pii_tool.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
LOG = open(os.path.join(S, "log.txt"), encoding="utf-8").read()


def make_rrn(first12):
    w = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    return first12 + str((11 - sum(int(a) * b for a, b in zip(first12, w)) % 11) % 10)


def kinds(text): return [k for _, _, k, _ in detect.find(text)]


def test_sample_log_kinds():
    assert sorted(kinds(LOG)) == sorted(["name", "mobile", "email", "rrn", "card", "ip", "address", "biz", "phone"])


def test_checksums():
    assert detect.luhn("4242 4242 4242 4242") and not detect.luhn("4242 4242 4242 4243")
    assert detect.biz_valid("123-45-67891") and not detect.biz_valid("123-45-67890")
    good = make_rrn("900101123456"); assert detect.rrn_checksum(good)
    t = f"번호 {good[:6]}-{good[6:]}"
    assert detect.find(t)[0][3] == "체크섬 일치"
    bad = good[:12] + str((int(good[12]) + 1) % 10)
    assert detect.find(f"{bad[:6]}-{bad[6:]}")[0][3] == "형식만 일치"      # 2020년 이후 발급분은 체크섬이 없을 수 있어 형식만 맞아도 가림


def test_false_positives_avoided():
    t = "주문번호 1234567890123 버전 1.2.3.4.5 날짜 2031-03-05 합계 14,500원 월 991301-1234567 가격 4242 4242 4242 4243"
    assert kinds(t) == []                                                   # 잘못된 월(13), Luhn 불일치, 점 5개짜리 IP
    assert kinds("홍길동님 안녕하세요") == []                                  # 라벨 없는 이름은 찾지 않음
    assert kinds("999.1.1.1") == []


def test_modes():
    t = "전화 010-1234-5678 메일 hong@example.com 카드 4242 4242 4242 4242 이름: 홍길동"
    m, c = mask.anonymize(t, "mask")
    assert "010-****-5678" in m and "h***@example.com" in m and "**** **** **** 4242" in m and "이름: 홍**" in m and c["mobile"] == 1
    k, _ = mask.anonymize(t, "token"); assert "[휴대폰]" in k and "[이메일]" in k and "[카드번호]" in k and "홍길동" not in k
    r, _ = mask.anonymize(t, "redact"); assert "5678" not in r and "████" in r
    h1, _ = mask.anonymize("010-1234-5678", "hash", "k1"); h2, _ = mask.anonymize("010 1234 5678", "hash", "k1"); h3, _ = mask.anonymize("010-1234-5678", "hash", "k2")
    assert h1 == h2 and h1 != h3 and "5678" not in h1                       # 같은 값 → 같은 가명(키가 같을 때)
    with pytest.raises(mask.MaskError, match="--key"): mask.anonymize("x", "hash")
    with pytest.raises(mask.MaskError): mask.anonymize("x", "weird")


def test_no_raw_values_leak_and_idempotent():
    out, cnt = mask.anonymize(LOG, "token")
    for raw in ("010-1234-5678", "hong@example.com", "900101-1234567", "4242 4242 4242 4242", "203.0.113.7", "홍길동", "123-45-67891", "02-123-4567"):
        assert raw not in out, raw
    assert mask.anonymize(out, "token")[0] == out and sum(cnt.values()) == 9
    assert "10:00:01" in out and "가입" in out                              # 개인정보 아닌 부분은 그대로


def test_overlap_resolution():
    t = "01012345678"                                                       # 휴대폰 하나로만 잡혀야 함
    assert kinds(t) == ["mobile"]
    assert kinds("4242424242424242") == ["card"]


def test_csv_mode_cellwise(tmp_path):
    out = tmp_path / "o.csv"
    assert main(["run", os.path.join(S, "users.csv"), "--out", str(out), "--mode", "token", "--csv"]) == 0
    rows = list(csv.reader(open(out, encoding="utf-8")))
    assert rows[1][2] == "[휴대폰]" and "[이메일]" in rows[1][3] and rows[1][0] == "1" and rows[0] == ["id", "name", "phone", "memo"]
    assert rows[1][1] == "홍길동"                                            # 라벨 없는 이름 칸은 못 찾음(알려진 한계)


def test_cli(tmp_path, capsys):
    assert main(["scan", os.path.join(S, "log.txt")]) == 0 and "주민번호: 1건" in capsys.readouterr().out
    out = tmp_path / "o.txt"
    assert main(["run", os.path.join(S, "log.txt"), "--out", str(out), "--mode", "hash"]) == 2   # 키 없음
    assert main(["run", os.path.join(S, "log.txt"), "--out", str(out), "--mode", "hash", "--key", "k"]) == 0
    assert main(["scan", str(tmp_path / "none.txt")]) == 2
