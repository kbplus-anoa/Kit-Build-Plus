import pytest

import kbp.export.csv_writer as csv_writer
import kbp.contracts.exportcsv as exportcsv
import kbp.export.question_table as question_table
import kbp.export.subject_table as subject_table


def subject(**kw):
    base = dict(participant_id=1, material_id=1, time_point="post",
                submit_seq=1, target_map_version="v1", fingerprint="fp1",
                mode="test", condition="exp", is_practice=0,
                correct_propositions=2, total_propositions=3,
                n_lacking=1, n_excessive=0, n_leaving=0, n_reversed=0,
                possibly_inaccurate=0, map_size=2, map_node_count=3,
                signal_isolated=0.1, signal_coverage=0.8,
                signal_concentration=0.5, signal_baseline=1.2)
    base.update(kw)
    return exportcsv.SubjectRow(**base)


def question(**kw):
    base = dict(participant_id=1, material_id=1, time_point="pre",
                submit_seq=1, target_map_version="v1",
                question_id="q1", correct=1,
                score=None, qtype="single", content_dimension="记忆")
    base.update(kw)
    return exportcsv.QuestionRow(**base)


def test_被试表列数与表头一致():
    payload = subject_table.build((subject(),))
    assert len(payload.rows[0]) == len(subject_table.HEADER)


def test_题级表列数与表头一致():
    payload = question_table.build((question(),))
    assert len(payload.rows[0]) == len(question_table.HEADER)


def cell(payload, name, row=0):
    """按列名取值：加列不再让下标错位。"""
    return payload.rows[row][payload.header.index(name)]


def test_FMS_由分子分母现算且量纲_0_到_100():
    payload = subject_table.build((subject(correct_propositions=2,
                                           total_propositions=4),))
    assert cell(payload, "fms") == 50.0


def test_分母为零时分数为零():
    payload = subject_table.build((subject(correct_propositions=0,
                                           total_propositions=0),))
    assert cell(payload, "fms") == 0.0


def test_表头含指纹列():
    """乙方案下同一教材在不同机器裁出的 kit 不同，须按指纹筛同批。"""
    payload = subject_table.build((subject(fingerprint="88977e96f49bd7d1"),))
    assert cell(payload, "fingerprint") == "88977e96f49bd7d1"


def test_有指纹时该列照抄():
    payload = subject_table.build((subject(),))
    assert cell(payload, "fingerprint") == "fp1"


def test_单选拼写正确():
    """回归：列名曾误拼成 is_partice，导出的表头对不上 CSV_PLAN。"""
    payload = subject_table.build((subject(),))
    assert "is_practice" in payload.header
    assert "is_partice" not in payload.header


def test_分子超过分母被拒():
    with pytest.raises(subject_table.TableError):
        subject_table.build((subject(correct_propositions=5,
                                     total_propositions=3),))


def test_未知组别被拒():
    with pytest.raises(subject_table.TableError):
        subject_table.build((subject(condition="other"),))


def test_布尔列越界被拒():
    with pytest.raises(subject_table.TableError):
        subject_table.build((subject(is_practice=2),))


def test_关联键为零被拒():
    with pytest.raises(subject_table.TableError):
        subject_table.build((subject(submit_seq=0),))


def test_空值导出为空串():
    assert csv_writer.quote(None) == ""


def test_布尔导出为零一():
    assert csv_writer.quote(True) == "1"
    assert csv_writer.quote(False) == "0"


def test_小数固定八位():
    assert csv_writer.quote(0.5) == "0.50000000"


def test_输出带_BOM():
    payload = subject_table.build((subject(),))
    data = csv_writer.to_csv(payload)
    assert data.startswith(b"\xef\xbb\xbf")


def test_编码不是_BOM_时拒绝():
    bad = exportcsv.CsvPayload(encoding="utf-8", header=("a",), rows=())
    with pytest.raises(csv_writer.ExportError):
        csv_writer.to_csv(bad)


def test_表头写入首行():
    payload = question_table.build((question(),))
    text = csv_writer.to_csv(payload).decode("utf-8-sig")
    assert text.splitlines()[0].startswith("participant_id")


def test_中文列名保留不转义():
    payload = question_table.build((question(),))
    text = csv_writer.to_csv(payload).decode("utf-8-sig")
    assert "内容维度" in text


def test_行宽不一致被拒():
    bad = exportcsv.CsvPayload(encoding=exportcsv.UTF8_BOM,
                               header=("a", "b"), rows=(("x",),))
    with pytest.raises(csv_writer.ExportError):
        csv_writer.check_width(bad)
