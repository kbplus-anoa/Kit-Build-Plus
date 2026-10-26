import pytest

import kbp.rebuild.rebuild_validate as v
import kbp.contracts.submission as submission
import kbp.contracts.targetmap as targetmap


def concept(cid, label):
    return targetmap.Concept(concept_id=cid, label=label)


def make_kit():
    return targetmap.Kit(map_version="v1",
                         concepts=(concept("c1", "记忆"), concept("c2", "短时记忆")),
                         connections=("包括", "属于"))


def prop(head, conn, tail):
    return submission.SubmittedProposition(head_id=head, connection=conn,
                                           tail_id=tail)


def test_合法命题通过():
    v.check_against_kit(make_kit(), (prop("c1", "包括", "c2"),))


def test_空命题集通过():
    v.check_against_kit(make_kit(), ())


def test_越界概念被拒绝():
    with pytest.raises(v.ValidationError):
        v.check_against_kit(make_kit(), (prop("c9", "包括", "c2"),))


def test_越界连接词被拒绝():
    with pytest.raises(v.ValidationError):
        v.check_against_kit(make_kit(), (prop("c1", "导致", "c2"),))


def test_自环被拒绝():
    with pytest.raises(v.ValidationError):
        v.check_against_kit(make_kit(), (prop("c1", "包括", "c1"),))


def test_重复命题被拒绝():
    p = prop("c1", "包括", "c2")
    with pytest.raises(v.ValidationError):
        v.check_against_kit(make_kit(), (p, p))


def test_反向命题不算重复():
    v.check_against_kit(make_kit(), (prop("c1", "包括", "c2"),
                                     prop("c2", "包括", "c1")))


def test_超量命题被拒绝():
    kit = targetmap.Kit(map_version="v1",
                        concepts=(concept("c1", "记忆"), concept("c2", "短时记忆")),
                        connections=("包括",))
    props = tuple(prop("c1", "包括", "c2") for _ in range(v.MAX_PROPOSITIONS + 1))
    with pytest.raises(v.ValidationError):
        v.check_against_kit(kit, props)


def test_模式只接受两值():
    v.check_mode(submission.TEST)
    v.check_mode(submission.STUDY)
    with pytest.raises(v.ValidationError):
        v.check_mode("exam")


def test_关联键必须为正整数():
    v.check_keys(1, 1, 1)
    with pytest.raises(v.ValidationError):
        v.check_keys(0, 1, 1)
    with pytest.raises(v.ValidationError):
        v.check_keys(1, 1, 0)
