import kbp.score.classify
import kbp.score.lookup
import kbp.contracts.report
import kbp.contracts.submission
import kbp.contracts.targetmap


def score(target: kbp.contracts.targetmap.TargetMap,
          sub: kbp.contracts.submission.Submission) -> kbp.contracts.report.ScoreResult:
    """一次提交 → 一份评分。分数 = 正确命题数 / 目标命题总数，无部分分。"""
    total = len(kbp.score.lookup.target_keys(target))
    correct = kbp.score.lookup.count_correct(target, sub.propositions)
    errors = kbp.score.classify.classify(target, sub.propositions)
    return kbp.contracts.report.ScoreResult(total_propositions=total,
                                            correct_propositions=correct,
                                            errors=errors)


def ratio(result: kbp.contracts.report.ScoreResult) -> float:
    """分数本身不进报告主结构，取用时才算，避免锁死公式。"""
    if result.total_propositions <= 0:
        return 0.0
    return result.correct_propositions / result.total_propositions


def summary(result: kbp.contracts.report.ScoreResult) -> dict:
    """按四类错误计数，供界面与 CSV 直接取。"""
    counts = {kind: 0 for kind in kbp.contracts.report.ERROR_KINDS}
    for chain in result.errors:
        counts[chain.kind] += 1
    return {
        "total": result.total_propositions,
        "correct": result.correct_propositions,
        "score": ratio(result),
        "lacking": counts[kbp.contracts.report.LACKING],
        "excessive": counts[kbp.contracts.report.EXCESSIVE],
        "leaving": counts[kbp.contracts.report.LEAVING],
        "reversed": counts[kbp.contracts.report.REVERSED],
    }
