import kbp.contracts.exportcsv
import kbp.contracts.submission


HEADER = ("participant_id", "material_id", "time_point", "submit_seq",
          "target_map_version", "question_id", "答对", "得分", "题型", "内容维度")


def build(rows) -> kbp.contracts.exportcsv.CsvPayload:
    """题级表：一人一题一时点一行，long 格式。"""
    check(rows)
    csv = kbp.contracts.exportcsv
    return csv.CsvPayload(encoding=csv.UTF8_BOM, header=HEADER,
                          rows=tuple(_row(r) for r in rows))


def check(rows: tuple[kbp.contracts.exportcsv.QuestionRow, ...]) -> None:
    for r in rows:
        reason = kbp.contracts.submission.check_key(
            r.participant_id, r.material_id, r.time_point, r.submit_seq)
        if reason:
            raise ValueError(reason)
        if not r.question_id.strip():
            raise ValueError("题号不得为空")
        if r.correct not in (0, 1):
            raise ValueError("答对只接受 0/1")


def _row(r) -> tuple:
    return (r.participant_id, r.material_id, r.time_point, r.submit_seq,
            r.target_map_version, r.question_id, r.correct, r.score, r.qtype,
            r.content_dimension)
