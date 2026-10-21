import os
import pytest
from pypdf import PdfReader
from exam_note import parser, pdfgen, outputs
from exam_note.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample", "note.md")
TEXT = open(SAMPLE, encoding="utf-8").read()


def blocks():
    b, p = parser.parse(TEXT)
    assert p == []
    return b


def test_sample_parses_cleanly():
    b = blocks()
    types = [x["type"] for x in b]
    assert types.count("h1") == 1 and types.count("h2") == 2 and types.count("h3") == 2
    assert types.count("terms") == 2 and types.count("table") == 1 and types.count("qa") == 2
    assert [x["a"] for x in b if x["type"] == "qa"] == ["pop", "기본키"]


def test_format_problems():
    bad = "\n".join(["# 제목", "# 또 제목", "## 장", "> 설명만 있음", "|a|b|", "|1|2|", "Q: 문제만 있음", "", "A: 짝 없는 정답"])
    _, p = parser.parse(bad)
    msg = " ".join(m for _, m in p)
    for key in ("제목(# )은 정확히 1개", "용어 박스", "구분선", "A:", "정답(A:)이 문제"):
        assert key in msg, key
    _, p2 = parser.parse("# 제목\n문장")
    assert any("장(## )이 하나도" in m for _, m in p2)
    _, p3 = parser.parse("# t\n## c\n|a|b|\n|---|---|\n|1|\n")
    assert any("칸 수" in m for _, m in p3)


def test_banned_phrases():
    assert parser.banned_phrases("이 노트로 합격 보장!") == ["합격 보장"]
    assert parser.banned_phrases("100% 합격 약속") and not parser.banned_phrases("정리 노트")


def test_pdf_pages_and_toc_numbers_match_real_pages(tmp_path):
    out = str(tmp_path / "n.pdf")
    info = pdfgen.build_pdf(blocks(), out, "print")
    r = PdfReader(out)
    assert info["pages"] == len(r.pages) >= 5  # 표지, 목차, 장2개 이상, 확인 문제, 정답
    outline = []
    def walk(items):
        for it in items:
            if isinstance(it, list): walk(it)
            else: outline.append((it.title, r.get_destination_page_number(it) + 1))
    walk(r.outline)
    recorded = [(t, pg) for _, t, pg in info["headings"]]
    assert outline == recorded                        # 실제 PDF 안 위치와 기록한 쪽번호가 같음
    assert [t for t, _ in outline][:3] == ["1장 자료구조", "1.1 스택과 큐", "2장 데이터베이스"]
    assert outline[-2][0] == "확인 문제" and outline[-1][0] == "정답"
    assert all(pg >= 3 for _, pg in outline)          # 표지(1), 목차(2) 뒤에 나옴


def test_korean_font_declared_and_text_in_stream(tmp_path):
    out = str(tmp_path / "n.pdf")
    info = pdfgen.build_pdf(blocks(), out, "print")
    r = PdfReader(out)
    fonts = set()
    for pg in r.pages:
        for f in (pg["/Resources"].get("/Font") or {}).values():
            fonts.add(f.get_object()["/BaseFont"])
    assert any("HYSMyeongJo" in str(f) for f in fonts) and info["embedded"] is False
    stream = b"".join(pg.get_contents().get_data() for pg in r.pages)
    # CID 글꼴은 글자를 UCS2로 넣는다. 영문 'push'는 \000p\000u\000s\000h 로 보인다 (한글 글리프 모양은 뷰어가 그림)
    assert b"\\000p\\000u\\000s\\000h" in stream


def test_two_layouts_differ(tmp_path):
    a = pdfgen.build_pdf(blocks(), str(tmp_path / "a.pdf"), "print")
    b = pdfgen.build_pdf(blocks(), str(tmp_path / "b.pdf"), "tablet")
    ra, rb = PdfReader(str(tmp_path / "a.pdf")), PdfReader(str(tmp_path / "b.pdf"))
    assert float(ra.pages[0].mediabox.width) != float(rb.pages[0].mediabox.width)
    with pytest.raises(ValueError): pdfgen.build_pdf(blocks(), str(tmp_path / "c.pdf"), "huge")


def test_missing_font_file(tmp_path):
    with pytest.raises(FileNotFoundError): pdfgen.build_pdf(blocks(), str(tmp_path / "x.pdf"), "print", "/no/such.ttf")


def test_preview_has_exact_page_count(tmp_path):
    src = str(tmp_path / "n.pdf"); pdfgen.build_pdf(blocks(), src, "print")
    n = outputs.preview_pdf(src, str(tmp_path / "p.pdf"), 3)
    assert n == 3 == len(PdfReader(str(tmp_path / "p.pdf")).pages)
    assert outputs.preview_pdf(src, str(tmp_path / "p2.pdf"), 999) == len(PdfReader(src).pages)
    with pytest.raises(ValueError): outputs.preview_pdf(src, str(tmp_path / "p3.pdf"), 0)


def test_watermark_on_every_page(tmp_path):
    src = str(tmp_path / "n.pdf"); pdfgen.build_pdf(blocks(), src, "print")
    dst = str(tmp_path / "w.pdf")
    n = outputs.watermark_pdf(src, dst, "홍길동")
    r = PdfReader(dst)
    assert n == len(r.pages)
    needle = "홍길동".encode("utf-16-be").hex().encode()   # 워터마크는 16진수 문자열로 들어간다
    for pg in r.pages:
        assert needle in pg.get_contents().get_data().replace(b"<", b"").replace(b">", b"").lower()
    clean = PdfReader(src)
    assert all(needle not in pg.get_contents().get_data().lower() for pg in clean.pages)  # 원본에는 없음
    with pytest.raises(ValueError): outputs.watermark_pdf(src, dst, "  ")


def test_cover_and_listing(tmp_path):
    c = outputs.cover_image(str(tmp_path / "c.png"), "정보처리 요약노트", "정보처리기사")
    assert c["size"] == (1200, 1600) and os.path.getsize(tmp_path / "c.png") > 1000
    text = outputs.listing_draft("제목", "시험", 12, 5)
    assert "미확인" in text and "합격 보장" not in text


def test_cli_end_to_end(tmp_path):
    out = tmp_path / "o"
    assert main(["build", "--manuscript", SAMPLE, "--out", str(out), "--exam", "정보처리기사",
                 "--preview-pages", "3", "--buyer", "홍길동", "--buyer", "김철수"]) == 0
    for f in ("note_print.pdf", "note_tablet.pdf", "preview_free.pdf", "cover.png", "listing_draft.txt"):
        assert (out / f).exists(), f
    assert len(PdfReader(str(out / "preview_free.pdf")).pages) == 3
    assert len([f for f in os.listdir(out) if f.startswith("note_print_")]) == 2


def test_cli_blocks_and_errors(tmp_path):
    bad = tmp_path / "b.md"; bad.write_text("# 제목\n## 장\n이 노트는 합격 보장입니다.\n", encoding="utf-8")
    out = tmp_path / "o"
    assert main(["build", "--manuscript", str(bad), "--out", str(out)]) == 1 and not out.exists()
    assert main(["check", "--manuscript", str(tmp_path / "none.md")]) == 2
    empty = tmp_path / "e.md"; empty.write_text("  \n")
    assert main(["check", "--manuscript", str(empty)]) == 2
