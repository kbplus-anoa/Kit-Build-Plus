import classify
import lookup
import report
import submission
import targetmap


def score(target: targetmap.TargetMap,
          sub: submission.Submission) -> report.ScoreResult:
    """一次提交 → 一份评分。分数 = 正确命题数 / 目标命题总数，无部分分。"""
    total = len(lookup.target_keys(target))
    correct = lookup.count_correct(target, sub.propositions)
    errors = classify.classify(target, sub.propositions)
    return report.ScoreResult(total_propositions=total,
                              correct_propositions=correct,
                              errors=errors)


def ratio(result: report.ScoreResult) -> float:
    """分数本身不进报告主结构，取用时才算，避免锁死公式。"""
    if result.total_propositions <= 0:
        return 0.0
    return result.correct_propositions / result.total_propositions


def summary(result: report.ScoreResult) -> dict:
    """按四类错误计数，供界面与 CSV 直接取。"""
    counts = {kind: 0 for kind in report.ERROR_KINDS}
    for chain in result.errors:
        counts[chain.kind] += 1
    return {
        "total": result.total_propositions,
        "correct": result.correct_propositions,
        "score": ratio(result),
        "lacking": counts[report.LACKING],
        "excessive": counts[report.EXCESSIVE],
        "leaving": counts[report.LEAVING],
        "reversed": counts[report.REVERSED],
    }
