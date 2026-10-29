"""开发者叠层：整份改写存在库里，读图时盖在冻结图上。"""

import sqlite3

import pytest

import kbp.contracts.targetmap as targetmap
import kbp.contracts.triple as triple
import kbp.kit.dev_overlay as dev_overlay

VOCAB = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括", "属于"))
CONCEPTS = (targetmap.Concept(concept_id="c1", label="记忆"),
            targetmap.Concept(concept_id="c2", label="短时记忆"),
            targetmap.Concept(concept_id="c3", label="长时记忆"))
PROPS = (targetmap.Proposition(head_id="c1", connection="包括", tail_id="c2"),
         targetmap.Proposition(head_id="c3", connection="属于", tail_id="c1"))


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    dev_overlay.ensure(connection)
    yield connection
    connection.close()


def frozen(version="v1"):
    return targetmap.TargetMap(map_version=version, vocab=VOCAB,
                               concepts=CONCEPTS[:2], propositions=PROPS[:1],
                               fingerprint="fp-1")


def overlay():
    return dev_overlay.Overlay(concepts=CONCEPTS,
                               connections=("包括", "属于"),
                               propositions=PROPS)


def test_没改过读回空(conn):
    assert dev_overlay.load(conn, 1, "v1") is None


def test_存了能原样读回(conn):
    dev_overlay.save(conn, 1, "v1", overlay(), "2026-10-29T10:00:00")
    back = dev_overlay.load(conn, 1, "v1")
    assert [c.label for c in back.concepts] == ["记忆", "短时记忆", "长时记忆"]
    assert [(p.head_id, p.connection, p.tail_id) for p in back.propositions] == \
        [("c1", "包括", "c2"), ("c3", "属于", "c1")]
    assert back.connections == ("包括", "属于")
    assert back.updated_at == "2026-10-29T10:00:00"


def test_再存一次整份覆盖(conn):
    dev_overlay.save(conn, 1, "v1", overlay(), "t1")
    small = dev_overlay.Overlay(concepts=CONCEPTS[:2],
                                connections=("包括",),
                                propositions=PROPS[:1])
    dev_overlay.save(conn, 1, "v1", small, "t2")
    back = dev_overlay.load(conn, 1, "v1")
    assert [c.label for c in back.concepts] == ["记忆", "短时记忆"]
    assert back.connections == ("包括",)
    assert back.updated_at == "t2"


def test_按教材与版本分开存(conn):
    dev_overlay.save(conn, 1, "v1", overlay(), "t1")
    assert dev_overlay.load(conn, 2, "v1") is None
    assert dev_overlay.load(conn, 1, "v2") is None


def test_撤销后回到没有(conn):
    dev_overlay.save(conn, 1, "v1", overlay(), "t1")
    dev_overlay.drop(conn, 1, "v1")
    assert dev_overlay.load(conn, 1, "v1") is None


def test_撤销没改过的也不报错(conn):
    dev_overlay.drop(conn, 1, "v1")
    assert dev_overlay.load(conn, 1, "v1") is None


def test_盖上去不改指纹与版本(conn):
    dev_overlay.save(conn, 1, "v1", overlay(), "t1")
    merged = dev_overlay.apply(frozen(), dev_overlay.load(conn, 1, "v1"))
    assert merged.fingerprint == "fp-1"
    assert merged.map_version == "v1"
    assert len(merged.concepts) == 3 and len(merged.propositions) == 2


def test_没有改写就原样返回():
    base = frozen()
    assert dev_overlay.apply(base, None) is base


@pytest.mark.parametrize("bad, reason", [
    (dev_overlay.Overlay(concepts=(), connections=("包括",), propositions=()),
     "概念不得为空"),
    (dev_overlay.Overlay(concepts=CONCEPTS, connections=(), propositions=()),
     "连接词不得为空"),
    (dev_overlay.Overlay(concepts=(CONCEPTS[0], CONCEPTS[0]),
                         connections=("包括",), propositions=()),
     "概念 id 重复"),
    (dev_overlay.Overlay(concepts=(CONCEPTS[0],
                                   targetmap.Concept(concept_id="c9",
                                                     label="记忆")),
                         connections=("包括",), propositions=()),
     "概念字面重复"),
    (dev_overlay.Overlay(concepts=CONCEPTS, connections=("包括", "包括"),
                         propositions=()),
     "连接词重复"),
    (dev_overlay.Overlay(concepts=CONCEPTS, connections=("包括",),
                         propositions=(targetmap.Proposition(
                             head_id="c1", connection="属于", tail_id="c2"),)),
     "命题用了不存在的连接词: 属于"),
    (dev_overlay.Overlay(concepts=CONCEPTS, connections=("包括",),
                         propositions=(targetmap.Proposition(
                             head_id="c1", connection="包括", tail_id="c9"),)),
     "命题用了不存在的概念: c1>c9"),
    (dev_overlay.Overlay(concepts=CONCEPTS, connections=("包括",),
                         propositions=(targetmap.Proposition(
                             head_id="c1", connection="包括", tail_id="c1"),)),
     "命题不允许自环: c1"),
    (dev_overlay.Overlay(concepts=CONCEPTS, connections=("包括",),
                         propositions=(PROPS[0], PROPS[0])),
     "命题重复: c1>包括>c2"),
])
def test_不成立就拒并说明原因(bad, reason):
    assert dev_overlay.check(bad) == reason


def test_不成立时库里的字一个字不动(conn):
    dev_overlay.save(conn, 1, "v1", overlay(), "t1")
    bad = dev_overlay.Overlay(concepts=(), connections=("包括",),
                              propositions=())
    with pytest.raises(dev_overlay.OverlayError):
        dev_overlay.save(conn, 1, "v1", bad, "t2")
    back = dev_overlay.load(conn, 1, "v1")
    assert len(back.concepts) == 3 and back.updated_at == "t1"


def test_空版本号拒存(conn):
    with pytest.raises(dev_overlay.OverlayError):
        dev_overlay.save(conn, 1, "", overlay(), "t1")
