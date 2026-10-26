import kbp.contracts.exportcsv


HEADER = ("participant_id", "material_id", "target_map_version", "session",
          "question_id", "time_point", "答对", "得分", "题型", "内容维度")


def build(rows) -> kbp.contracts.exportcsv.CsvPayload:
    """题级表：一人一题一时点一行，long 格式。"""
    check(rows)
    csv = kbp.contracts.exportcsv
    return csv.CsvPayload(encoding=csv.UTF8_BOM, header=HEADER,
                          rows=tuple(_row(r) for r in rows))


def check(rows: tuple[kbp.contracts.exportcsv.QuestionRow, ...]) -> None:
    for r in rows:
        if r.participant_id < 1 or r.material_id < 1 or r.session < 1:
            raise ValueError("关联键须为正整数")
        if not r.question_id.strip():
            raise ValueError("题号不得为空")
        if r.correct not in (0, 1):
            raise ValueError("答对只接受 0/1")


def _row(r) -> tuple:
    return (r.participant_id, r.material_id, r.target_map_version, r.session,
            r.question_id, r.time_point, r.correct, r.score, r.qtype,
            r.content_dimension)
