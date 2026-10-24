from dataclasses import FrozenInstanceError

import pytest

import exportcsv
import report
import submission
import textdoc
import triple


def make_vocab():
    return triple.Vocab(vocab_id="心理学", vocab_version="v1",
                        connections=("属于", "导致"))


def test_textdoc_枚举取值固定():
    assert textdoc.TEXT_SOURCES == ("TEXT_LAYER", "EPUB", "OCR_CLOUD")


def test_模式枚举只有测试与学习():
    assert submission.MODES == ("test", "study")


def test_错误链四类固定():
    assert report.ERROR_KINDS == ("lacking", "excessive", "leaving", "reversed")


def test_csv_编码固定为带_BOM():
    assert exportcsv.UTF8_BOM == "utf-8-sig"


def test_契约不可变():
    vocab = make_vocab()
    with pytest.raises(FrozenInstanceError):
        vocab.vocab_id = "物理学"


def test_词表判定只暴露签名不含实现():
    import inspect
    names = list(inspect.signature(triple.in_vocab).parameters)
    assert names == ["vocab", "connection"]


def test_评分比率契约签名稳定():
    import inspect
    names = list(inspect.signature(report.ratio).parameters)
    assert names == ["result"]


def test_导入契约不产生副作用():
    assert isinstance(make_vocab(), triple.Vocab)
