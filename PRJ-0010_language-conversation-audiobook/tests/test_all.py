import csv, math, os, struct, subprocess, wave
import pytest
from pypdf import PdfReader
from audiobook_builder import sheet, tts, audio, textbook, listing
from audiobook_builder.cli import main, load_cfg

CFG = load_cfg()
HEAD = ["no", "situation", "text", "meaning", "pronunciation"]
ROWS = [["1", "공항", "Where is the gate?", "게이트는 어디예요?", "웨어"],
        ["2", "공항", "I lost my bag.", "가방을 잃어버렸어요.", ""],
        ["3", "식당", "The bill, please.", "계산서 주세요.", ""]]


def write_csv(path, rows, head=HEAD):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=nw=1:nk=1", path], capture_output=True, text=True, check=True).stdout)


def test_sheet_problems(tmp_path):
    rows = [dict(zip(HEAD, r)) for r in ROWS]
    assert sheet.check_rows(rows, 120) == []
    bad = [dict(zip(HEAD, ["1", "공항", "Hello", "안녕", ""])), dict(zip(HEAD, ["1", "공항", "hello", "", ""])),
           dict(zip(HEAD, ["x", "식당", "a" * 130, "뜻", ""]))]
    msgs = " ".join(m for _, m in sheet.check_rows(bad, 120))
    for key in ("겹칩니다", "같은 문장", "비어 있습니다", "숫자여야", "너무 깁니다"):
        assert key in msgs


def test_sheet_read_errors(tmp_path):
    with pytest.raises(FileNotFoundError): sheet.read_sheet(str(tmp_path / "no.csv"))
    write_csv(tmp_path / "e.csv", [])
    with pytest.raises(ValueError): sheet.read_sheet(str(tmp_path / "e.csv"))
    write_csv(tmp_path / "h.csv", [["1", "a"]], head=["no", "situation"])
    with pytest.raises(ValueError): sheet.read_sheet(str(tmp_path / "h.csv"))


def test_chapters_order():
    rows = [dict(zip(HEAD, r)) for r in ROWS]
    assert list(sheet.chapters(rows)) == ["공항", "식당"]


def test_chapter_duration_and_gap(tmp_path):
    rows = [dict(zip(HEAD, r)) for r in ROWS[:2]]
    work = tmp_path / "w"; work.mkdir(); out = tmp_path / "o"; out.mkdir()
    info = audio.build_chapter(1, "공항", rows, tts.SilentProvider(CFG), CFG, str(work), str(out))
    d1, d2 = max(0.5, .06 * len(rows[0]["text"])), max(0.5, .06 * len(rows[1]["text"]))
    exp = d1 + d2 + 2 * CFG["gap_sec"]
    assert abs(info["seconds"] - exp) < 0.02
    assert info["starts"] == [0.0, round(d1 + CFG["gap_sec"], 2)]
    assert abs(dur(info["mp3"]) - exp) < 0.3  # mp3 인코딩 여유


def test_folder_provider(tmp_path):
    rec = tmp_path / "rec"; rec.mkdir()
    tts.write_silence(str(rec / "1.wav"), 1.0, 16000)  # 다른 샘플레이트 → 변환돼야 함
    prov = tts.FolderProvider(CFG, folder=str(rec))
    out = str(tmp_path / "o.wav")
    prov.synth({"no": "1", "text": "x"}, out)
    assert abs(audio.wav_seconds(out) - 1.0) < 0.05
    with pytest.raises(FileNotFoundError): prov.synth({"no": "9", "text": "x"}, out)
    with pytest.raises(FileNotFoundError): tts.FolderProvider(CFG, folder=str(tmp_path / "none"))


def test_provider_errors():
    with pytest.raises(ValueError): tts.get_provider("zzz", CFG)
    try:
        import edge_tts  # noqa
    except ImportError:
        with pytest.raises(RuntimeError, match="edge-tts"): tts.get_provider("edge-tts", CFG)


def test_pdf_pages_and_listing(tmp_path):
    rows = [dict(zip(HEAD, r)) for r in ROWS]
    ch = [("공항", rows[:2]), ("식당", rows[2:])]
    out = str(tmp_path / "t.pdf")
    n = textbook.build_pdf(out, "제목", ch, CFG["pdf_font"])
    assert n == len(PdfReader(out).pages) >= 2
    many = [dict(zip(HEAD, [str(i), "공항", f"sentence {i}", "뜻", "발음"])) for i in range(1, 80)]
    assert textbook.build_pdf(str(tmp_path / "m.pdf"), "t", [("공항", many)], CFG["pdf_font"]) > 3
    info = [("공항", rows[:2], {"seconds": 10}), ("식당", rows[2:], {"seconds": 5})]
    text = listing.draft("제목", info, "silent")
    assert "3문장" in text and "시험용" in text
    assert "약관" in listing.draft("제목", info, "edge-tts")


def test_cli_end_to_end(tmp_path):
    write_csv(tmp_path / "s.csv", ROWS)
    out = tmp_path / "out"
    assert main(["build", "--sheet", str(tmp_path / "s.csv"), "--out", str(out), "--gap", "1.0"]) == 0
    mp3s = sorted(f for f in os.listdir(out) if f.endswith(".mp3"))
    assert len(mp3s) == 2 and all(os.path.exists(out / f) for f in ("toc.txt", "textbook.pdf", "listing_draft.txt"))
    toc = (out / "toc.txt").read_text(encoding="utf-8")
    assert "1. 공항" in toc and "2. 식당" in toc


def test_cli_blocks_bad_sheet(tmp_path):
    write_csv(tmp_path / "s.csv", ROWS + [["3", "식당", "The bill, please.", "중복", ""]])
    out = tmp_path / "out"
    assert main(["build", "--sheet", str(tmp_path / "s.csv"), "--out", str(out)]) == 1 and not out.exists()
    assert main(["check", "--sheet", str(tmp_path / "none.csv")]) == 2
