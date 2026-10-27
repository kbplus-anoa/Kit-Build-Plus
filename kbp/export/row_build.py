"""把一次提交折算成被试级快照：只搬运上游结果，不再算一遍分。

分数、四类错误计数都来自 score 的结果；描述统计只数命题与概念。
组别与抽崩信号来自提交端（裁 kit 时已经给过），这里不猜默认值。
"""

import kbp.contracts.exportcsv
import kbp.contracts.report
import kbp.contracts.submission


def subject_row(sub: kbp.contracts.submission.Submission,
                result: kbp.contracts.report.ScoreResult, *,
                condition: str = "", is_practice: int = 0,
                possibly_inaccurate: int = 0, signals: tuple = ()) -> object:
    """一次提交 → 被试级一行；signals 顺序为孤立率/覆盖率/集中度/基线偏离。"""
    counts = _counts(result)
    isolated, coverage, concentration, baseline = _signals(signals)
    return kbp.contracts.exportcsv.SubjectRow(
        participant_id=sub.participant_id, material_id=sub.material_id,
        time_point=sub.time_point, submit_seq=sub.submit_seq,
        target_map_version=sub.map_version, fingerprint=sub.fingerprint,
        mode=sub.mode, condition=condition, is_practice=is_practice,
        correct_propositions=result.correct_propositions,
        total_propositions=result.total_propositions,
        n_lacking=counts[kbp.contracts.report.LACKING],
        n_excessive=counts[kbp.contracts.report.EXCESSIVE],
        n_leaving=counts[kbp.contracts.report.LEAVING],
        n_reversed=counts[kbp.contracts.report.REVERSED],
        possibly_inaccurate=possibly_inaccurate,
        map_size=len(sub.propositions),
        map_node_count=_nodes(sub), signal_isolated=isolated,
        signal_coverage=coverage, signal_concentration=concentration,
        signal_baseline=baseline)


def _counts(result) -> dict:
    counts = {kind: 0 for kind in kbp.contracts.report.ERROR_KINDS}
    for chain in result.errors:
        counts[chain.kind] += 1
    return counts


def _nodes(sub) -> int:
    used = set()
    for p in sub.propositions:
        used.add(p.head_id)
        used.add(p.tail_id)
    return len(used)


def _signals(signals: tuple) -> tuple:
    """四条信号按固定顺序；缺项留 None，不做插值也不填 0。"""
    values = tuple(signals) + (None,) * 4
    return values[0], values[1], values[2], values[3]
