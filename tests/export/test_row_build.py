"""快照折算：分数与错误计数从评分结果搬运，描述统计只数结构。"""


import kbp.contracts.report as report
import kbp.contracts.submission as submission
import kbp.export.row_build as row_build


def sub(**kw):
    base = dict(map_version="v1", fingerprint="fp1", mode="test",
                propositions=(),
                started_at="2026-10-27T10:00:00",
                submitted_at="2026-10-27T10:05:00",
                participant_id=1, material_id=1, time_point="post",
                submit_seq=1)
    base.update(kw)
    return submission.Submission(**base)


def prop(head, tail):
    return submission.SubmittedProposition(
        head_id=head, connection="包括", tail_id=tail)


def chain(kind, head, tail):
    return report.ErrorChain(kind, head, "包括", tail)


def test_四类错误各数各的():
    result = report.ScoreResult(
        total_propositions=4, correct_propositions=1,
        errors=(chain(report.LACKING, "a", "b"),
                chain(report.LACKING, "c", "d"),
                chain(report.EXCESSIVE, "e", "f"),
                chain(report.LEAVING, "g", "h"),
                chain(report.REVERSED, "i", "j")))
    row = row_build.subject_row(sub(), result)
    assert (row.n_lacking, row.n_excessive, row.n_leaving,
            row.n_reversed) == (2, 1, 1, 1)


def test_分子分母原样搬运不重算():
    result = report.ScoreResult(total_propositions=3, correct_propositions=2,
                                errors=())
    row = row_build.subject_row(sub(), result)
    assert (row.correct_propositions, row.total_propositions) == (2, 3)


def test_命题数与去重节点数分开数():
    row = row_build.subject_row(
        sub(propositions=(prop("a", "b"), prop("b", "c"))),
        report.ScoreResult(total_propositions=3, correct_propositions=1,
                           errors=()))
    assert row.map_size == 2 and row.map_node_count == 3


def test_四条信号按固定顺序落列():
    row = row_build.subject_row(
        sub(), report.ScoreResult(3, 1, ()),
        signals=(0.1, 0.8, 0.5, 1.2))
    assert (row.signal_isolated, row.signal_coverage,
            row.signal_concentration, row.signal_baseline) == (
                0.1, 0.8, 0.5, 1.2)


def test_缺项信号留空不填零():
    row = row_build.subject_row(sub(), report.ScoreResult(3, 1, ()),
                                signals=(0.1,))
    assert row.signal_coverage is None and row.signal_baseline is None


def test_组别与抽崩标记来自提交端():
    row = row_build.subject_row(sub(participant_id=7),
                                report.ScoreResult(3, 1, ()),
                                condition="con", is_practice=1,
                                possibly_inaccurate=1)
    assert (row.condition, row.is_practice,
            row.possibly_inaccurate) == ("con", 1, 1)
    assert (row.participant_id, row.submit_seq) == (7, 1)
