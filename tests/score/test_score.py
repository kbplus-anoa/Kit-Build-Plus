import kbp.contracts.report as report
import kbp.score.score_service as svc
import kbp.contracts.submission as submission
import kbp.contracts.targetmap as targetmap
import kbp.contracts.triple as triple


def concept(cid, label):
    return targetmap.Concept(concept_id=cid, label=label)


def prop(head, conn, tail):
    return targetmap.Proposition(head_id=head, connection=conn, tail_id=tail)


def make_target():
    """目标图：c1 记忆 --包括--> c2 短时记忆；c2 --属于--> c3 记忆系统。"""
    v = triple.Vocab(vocab_id="心理学", vocab_version="v1",
                     connections=("包括", "属于", "导致"))
    return targetmap.TargetMap(
        map_version="v1", vocab=v,
        concepts=(concept("c1", "记忆"), concept("c2", "短时记忆"),
                  concept("c3", "记忆系统")),
        propositions=(prop("c1", "包括", "c2"), prop("c2", "属于", "c3")))


def sprop(head, conn, tail):
    return submission.SubmittedProposition(head_id=head, connection=conn,
                                           tail_id=tail)


def make_sub(props):
    return submission.Submission(map_version="v1", mode=submission.TEST,
                                 propositions=tuple(props), started_at="",
                                 submitted_at="2026-10-25T10:00:00",
                                 participant_id=1, material_id=1, session=1)


def kinds(result):
    return [c.kind for c in result.errors]


def test_全对得满分():
    r = svc.score(make_target(), make_sub([sprop("c1", "包括", "c2"),
                                           sprop("c2", "属于", "c3")]))
    assert (r.correct_propositions, r.total_propositions) == (2, 2)
    assert svc.ratio(r) == 1.0
    assert r.errors == ()


def test_空提交得零分且全部缺失():
    r = svc.score(make_target(), make_sub([]))
    assert r.correct_propositions == 0
    assert svc.ratio(r) == 0.0
    assert kinds(r) == [report.LACKING, report.LACKING]


def test_方向反转单独成类():
    r = svc.score(make_target(), make_sub([sprop("c2", "包括", "c1")]))
    assert kinds(r).count(report.REVERSED) == 1
    assert report.LACKING in kinds(r)


def test_方向反转不再算多余():
    r = svc.score(make_target(), make_sub([sprop("c2", "包括", "c1")]))
    assert report.EXCESSIVE not in kinds(r)


def test_方向反转不再算游离():
    r = svc.score(make_target(), make_sub([sprop("c2", "包括", "c1")]))
    assert report.LEAVING not in kinds(r)


def test_连接词用错算游离():
    """c1→c2 应走"包括"，学生写了"导致"。"""
    r = svc.score(make_target(), make_sub([sprop("c1", "导致", "c2")]))
    assert report.LEAVING in kinds(r)


def test_游离不再算多余():
    r = svc.score(make_target(), make_sub([sprop("c1", "导致", "c2")]))
    assert report.EXCESSIVE not in kinds(r)


def test_概念对不存在算多余():
    r = svc.score(make_target(), make_sub([sprop("c1", "属于", "c3")]))
    assert report.EXCESSIVE in kinds(r)


def test_多余不再是游离():
    r = svc.score(make_target(), make_sub([sprop("c1", "属于", "c3")]))
    assert report.LEAVING not in kinds(r)


def test_每条错写只归一类():
    props = [sprop("c2", "包括", "c1"), sprop("c1", "导致", "c2"),
             sprop("c1", "属于", "c3")]
    r = svc.score(make_target(), make_sub(props))
    wrong = [c for c in r.errors if c.kind != report.LACKING]
    assert len(wrong) == 3
    assert len({(c.head_id, c.connection, c.tail_id) for c in wrong}) == 3


def test_错误不影响分数():
    good = svc.score(make_target(), make_sub([sprop("c1", "包括", "c2")]))
    noisy = svc.score(make_target(), make_sub([sprop("c1", "包括", "c2"),
                                               sprop("c1", "导致", "c2"),
                                               sprop("c2", "包括", "c1")]))
    assert noisy.correct_propositions == good.correct_propositions


def test_重复提交同一条不重复计分():
    r = svc.score(make_target(), make_sub([sprop("c1", "包括", "c2"),
                                           sprop("c1", "包括", "c2")]))
    assert r.correct_propositions == 1


def test_空目标图分母为零不除错():
    empty = targetmap.TargetMap(map_version="v1", vocab=make_target().vocab,
                                concepts=(), propositions=())
    r = svc.score(empty, make_sub([]))
    assert svc.ratio(r) == 0.0


def test_摘要计数与错误链一致():
    r = svc.score(make_target(), make_sub([sprop("c2", "包括", "c1")]))
    s = svc.summary(r)
    assert s["reversed"] == 1
    assert s["lacking"] == 2
    assert s["score"] == 0.0
