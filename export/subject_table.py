import exportcsv


HEADER = ("participant_id", "material_id", "target_map_version", "session",
          "mode", "condition", "is_partice", "total_propositions",
          "correct_propositions", "score", "n_lacking", "n_excessive",
          "n_leaving", "n_reversed", "possibly_inaccurate", "map_size",
          "map_node_count", "孤立概念率", "连接词覆盖率", "概念集中度",
          "基线偏离度")


class TableError(ValueError):
    """被试级表的数据不合法。"""


def build(rows: tuple[exportcsv.SubjectRow, ...]) -> exportcsv.CsvPayload:
    """被试级表：一人一次提交一行。分数现算，分子分母来自上游。"""
    check(rows)
    return exportcsv.CsvPayload(encoding=exportcsv.UTF8_BOM, header=HEADER,
                                rows=tuple(_row(r) for r in rows))


def check(rows: tuple[exportcsv.SubjectRow, ...]) -> None:
    for r in rows:
        _check_one(r)


def _check_one(r) -> None:
    if r.participant_id < 1 or r.material_id < 1 or r.session < 1:
        raise TableError("关联键须为正整数")
    if r.condition not in exportcsv.CONDITIONS:
        raise TableError("未知组别: " + str(r.condition))
    if r.total_propositions < 0:
        raise TableError("分母不得为负")
    if not 0 <= r.correct_propositions <= r.total_propositions:
        raise TableError("分子须落在 0~分母")
    for value in (r.is_practice, r.possibly_inaccurate):
        if value not in (0, 1):
            raise TableError("布尔列只接受 0/1")
    for value in (r.map_size, r.map_node_count):
        if value < 0:
            raise TableError("描述统计不得为负")


def _row(r) -> tuple:
    total = r.total_propositions
    ratio = _ratio(r.correct_propositions, total)
    return (r.participant_id, r.material_id, r.target_map_version, r.session,
            r.mode, r.condition, r.is_practice, total,
            r.correct_propositions, ratio, r.n_lacking, r.n_excessive,
            r.n_leaving, r.n_reversed, r.possibly_inaccurate,
            r.map_size, r.map_node_count, r.signal_isolated,
            r.signal_coverage, r.signal_concentration, r.signal_baseline)


def _ratio(correct: int, total: int) -> float:
    """分数现算，不在导出层另存一份，避免与屏幕分数不一致。"""
    return 0.0 if total <= 0 else correct / total
