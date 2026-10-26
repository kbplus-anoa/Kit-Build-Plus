import inspect

import pytest
from dataclasses import FrozenInstanceError

import kbp.contracts.targetbank as targetbank
import kbp.contracts.targetmap as targetmap
import kbp.contracts.triple as triple


def make_map(map_version="v1", fingerprint="fp1"):
    vocab = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                         connections=("属于",))
    concepts = (targetmap.Concept(concept_id="c1", label="短时记忆"),)
    return targetmap.TargetMap(map_version=map_version, vocab=vocab,
                               concepts=concepts, propositions=(),
                               fingerprint=fingerprint)


def make_entry(**kw):
    base = dict(material_id=1, vocab_version="v1",
                source=targetbank.ADJUDICATED, in_use=False,
                created_at="2026-10-26", target_map=make_map())
    base.update(kw)
    return targetbank.BankEntry(**base)


def test_来源枚举两个值():
    assert targetbank.SOURCES == ("adjudicated", "auto")


def test_登记项合法时无原因():
    assert targetbank.check_entry(make_entry()) == ""


def test_教材编号须为正整数():
    assert "material_id" in targetbank.check_entry(make_entry(material_id=0))


def test_词表版本不得为空():
    assert "词表版本" in targetbank.check_entry(make_entry(vocab_version=""))


def test_未知来源被拒():
    assert "未知来源" in targetbank.check_entry(make_entry(source="manual"))


def test_入库时间不得为空():
    assert "入库时间" in targetbank.check_entry(make_entry(created_at=""))


def test_冻结图必须带指纹():
    entry = make_entry(target_map=make_map(fingerprint=""))
    assert "内容指纹" in targetbank.check_entry(entry)


def test_版本号不得为空():
    entry = make_entry(target_map=make_map(map_version=""))
    assert "版本号" in targetbank.check_entry(entry)


def test_按指纹认同一张图():
    assert targetbank.same_map(make_entry(), "fp1")
    assert not targetbank.same_map(make_entry(), "fp2")
    assert not targetbank.same_map(make_entry(), "")


def test_未算指纹的图不算命中():
    entry = make_entry(target_map=make_map(fingerprint=""))
    assert not targetbank.same_map(entry, "")


def test_登记项不可变():
    with pytest.raises(FrozenInstanceError):
        make_entry().in_use = True


def test_库协议方法名固定():
    names = [n for n in targetbank.TargetMapBank.__dict__ if not n.startswith("_")]
    assert names == ["register", "by_fingerprint", "latest", "version_exists",
                     "mark_in_use"]


def test_按指纹查签名稳定():
    params = inspect.signature(targetbank.TargetMapBank.by_fingerprint).parameters
    assert list(params) == ["self", "material_id", "fingerprint"]
