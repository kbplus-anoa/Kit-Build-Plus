import pytest

import onnx_uie
import triple


def make_vocab(conns=("属于", "导致")):
    return triple.Vocab(vocab_id="心理学", vocab_version="v1",
                        connections=tuple(conns))


def span(text, start, end, prob):
    return {"text": text, "start": start, "end": end, "probability": prob}


def test_特殊_token_id_按词表取():
    assert onnx_uie.CLS_ID == 1
    assert onnx_uie.SEP_ID == 2


def test_缺权重时明确报错(tmp_path, monkeypatch):
    monkeypatch.setenv("KBP_UIE_DIR", str(tmp_path))
    with pytest.raises(onnx_uie.OnnxUnavailable):
        onnx_uie.OnnxUieExtractor().extract("文本", {"概念": ["属于"]})


def test_句类型区分_prompt_与正文():
    feeds = onnx_uie._feeds([1, 371, 366, 2, 749, 1094], split_at=4)
    assert feeds["token_type_ids"][0].tolist() == [0, 0, 0, 0, 1, 1]


def test_编码含_cls_与_sep():
    class FakeTk:
        def encode(self, s, add_special_tokens=False):
            class E:
                ids = [10, 11]
                offsets = [(0, 1), (1, 2)]
            return E()

    ids, _, split = onnx_uie._encode(FakeTk(), "属于", "正文")
    assert ids[0] == onnx_uie.CLS_ID
    assert ids[-1] == onnx_uie.SEP_ID
    assert split == 4


def test_start_与_end_按下标配对():
    paired = onnx_uie._pair([(3, 0.9), (7, 0.8)], [(4, 0.95), (8, 0.85)])
    assert len(paired) == 2


def test_结束下标不得早于起始下标():
    assert onnx_uie._pair([(5, 0.9)], [(2, 0.9)]) == []


def test_越界连接词被丢弃():
    raw = [{"导致": [span("衰退", 0, 2, 0.9)],
            "包含": [span("记忆", 3, 5, 0.9)]}]
    assert onnx_uie.to_triples(raw, "衰退记忆", make_vocab()) == []


def test_两个概念生成两条有向命题():
    raw = [{"属于": [span("记忆", 0, 2, 0.9), span("认知", 3, 5, 0.8)]}]
    got = onnx_uie.to_triples(raw, "记忆认知", make_vocab())
    assert len(got) == 2
    assert {t.head for t in got} == {"记忆", "认知"}


def test_单概念无法成对():
    raw = [{"属于": [span("记忆", 0, 2, 0.9)]}]
    assert onnx_uie.to_triples(raw, "记忆", make_vocab()) == []


def test_未填_text_的_span_按正文切片补齐():
    got = onnx_uie._fill(span(None, 2, 4, 0.9), "零一记忆")
    assert got["text"] == "记忆"
