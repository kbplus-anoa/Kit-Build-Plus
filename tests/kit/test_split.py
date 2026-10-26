import pytest

import kbp.kit.split as split
import kbp.contracts.targetmap as targetmap


def concept(cid, label):
    return targetmap.Concept(concept_id=cid, label=label)


def prop(head, conn, tail):
    return targetmap.Proposition(head_id=head, connection=conn, tail_id=tail)


def make_target(props, extra_concepts=()):
    import kbp.contracts.triple
    v = kbp.contracts.triple.Vocab(vocab_id="心理学", vocab_version="v1",
                                   connections=("属于", "导致", "包括"))
    concepts = [concept("c1", "记忆"), concept("c2", "短时记忆")]
    concepts += [concept(cid, label) for cid, label in extra_concepts]
    return targetmap.TargetMap(map_version="v1", vocab=v,
                               concepts=tuple(concepts),
                               propositions=tuple(props))


def test_拆出概念与连接词():
    k = split.split(make_target([prop("c1", "包括", "c2")]))
    assert [c.label for c in k.concepts] == ["记忆", "短时记忆"]
    assert k.connections == ("包括",)


def test_未被命题用到的概念不进_kit():
    t = make_target([prop("c1", "包括", "c2")],
                    extra_concepts=(("c9", "长时记忆"),))
    k = split.split(t)
    assert "c9" not in [c.concept_id for c in k.concepts]


def test_未被用到的连接词不进_kit():
    k = split.split(make_target([prop("c1", "包括", "c2")]))
    assert "属于" not in k.connections
    assert "导致" not in k.connections


def test_连接词按首次出现顺序():
    t = make_target([prop("c1", "包括", "c2"),
                     prop("c2", "属于", "c1"),
                     prop("c1", "包括", "c2")])
    assert split.split(t).connections == ("包括", "属于")


def test_空目标图拒绝拆分():
    t = make_target([])
    t = targetmap.TargetMap(map_version="v1", vocab=t.vocab,
                            concepts=(), propositions=())
    with pytest.raises(split.SplitError):
        split.split(t)


def test_无命题时拒绝拆分():
    t = targetmap.TargetMap(map_version="v1",
                            vocab=make_target([]).vocab,
                            concepts=(concept("c1", "记忆"),),
                            propositions=())
    with pytest.raises(split.SplitError):
        split.split(t)


def test_拆出的_kit_不带任何连接信息():
    k = split.split(make_target([prop("c1", "包括", "c2")]))
    assert not hasattr(k, "propositions")


def test_相同目标图拆出相同指纹():
    t = make_target([prop("c1", "包括", "c2")])
    assert split.kit_signature(split.split(t)) == split.kit_signature(split.split(t))


def test_连接词顺序不影响指纹():
    a = make_target([prop("c1", "包括", "c2")])
    b = make_target([prop("c1", "包括", "c2")])
    assert split.kit_signature(split.split(a)) == split.kit_signature(split.split(b))
