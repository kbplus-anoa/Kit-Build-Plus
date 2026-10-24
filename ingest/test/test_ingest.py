import zipfile

import pytest

import detect
import epub
import ocr
import ingest_service as service


def test_按魔数识别_pdf(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"%PDF-1.4 rest")
    assert detect.sniff(str(p)) == detect.PDF


def test_扩展名兜底识别_txt(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"no magic here")
    assert detect.sniff(str(p)) == detect.TXT


def test_未知格式抛错(tmp_path):
    p = tmp_path / "a.docx"
    p.write_bytes(b"zzz")
    with pytest.raises(ValueError):
        service.ingest(str(p))


def test_txt_读取保留原文(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes("概念图\n正文".encode("utf-8"))
    doc = service.ingest(str(p))
    assert doc.text == "概念图\n正文"
    assert doc.has_ocr is False


def test_txt_非_utf8_回退_gb18030(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes("中文".encode("gb18030"))
    assert service.ingest(str(p)).text == "中文"


def test_剥离标签只留文本():
    html = "<p>概念<em>图</em></p>"
    assert "概念" in epub.strip_tags(html)
    assert "<p>" not in epub.strip_tags(html)


def test_空_epub_返回空串(tmp_path):
    p = tmp_path / "a.epub"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("META-INF/container.xml",
                   '<container><rootfiles><rootfile full-path="c.opf"/></rootfiles></container>')
        z.writestr("c.opf", "<package/>")
    assert epub.read_epub(str(p)) == ""


def test_无_token_时_ocr_明确报错(monkeypatch):
    monkeypatch.delenv("MINERU_TOKEN", raising=False)
    with pytest.raises(ocr.MinerUUnavailable):
        ocr.upload_and_parse("/tmp/x.pdf", "x.pdf")


def test_扫描判定_文本稀疏算扫描件():
    assert _scanned([""] * 4) is True
    assert _scanned(["x" * 50] * 4) is False


def _scanned(pages):
    import pdf
    return pdf._looks_scanned(pages)
