from dataclasses import dataclass

UTF8_BOM = "utf-8-sig"

EXP = "exp"
CON = "con"

CONDITIONS = (EXP, CON)

MAX_SIGNAL = 1.0


@dataclass(frozen=True)
class SubjectRow:
    """export 契约：被试级一行，只读 score 结果不重算分。

    字段与 CSV_PLAN 的 A/B/C/D/E/F 节逐列对应，派生量（score）由 export 现算，
    但原始量（分子分母）必须来自上游，不得在导出时反推。
    """

    participant_id: int  # 被试顺序编号；不可空，>=1
    material_id: int  # 教材顺序编号；不可空，>=1
    target_map_version: str  # 目标图版本，如 v1；不可空
    session: int  # 场次，含练习；不可空，>=1
    mode: str  # 模式枚举 test/study；不可空
    condition: str  # 组别枚举，取值见 CONDITIONS；不可空
    is_practice: int  # 是否练习场次，0/1；不可空
    correct_propositions: int  # 评分分子；单位：条；不可空
    total_propositions: int  # 评分分母；单位：条；不可空
    n_lacking: int  # 缺失连接数；单位：条；不可空
    n_excessive: int  # 多余连接数；单位：条；不可空
    n_leaving: int  # 游离连接数；单位：条；不可空
    n_reversed: int  # 方向反转数；单位：条；不可空
    possibly_inaccurate: int  # 抽崩标记，0/1；不可空
    map_size: int  # 学生建出的命题数，含错误；单位：条；不可空
    map_node_count: int  # 学生用到的概念数；单位：个；不可空
    signal_isolated: float  # 孤立概念率，0~1；可空（未触发抽崩检测时为空）
    signal_coverage: float  # 连接词覆盖率，0~1；可空
    signal_concentration: float  # 概念集中度，0~1；可空
    signal_baseline: float  # 基线偏离度，Z 分数，可为负；可空


@dataclass(frozen=True)
class QuestionRow:
    """export 契约：题级一行，long 格式，一人一题一时点。"""

    participant_id: int  # 被试顺序编号；不可空，>=1
    material_id: int  # 教材顺序编号；不可空，>=1
    target_map_version: str  # 目标图版本；不可空
    session: int  # 场次；不可空，>=1
    question_id: str  # 题号，同卷内唯一；不可空
    time_point: str  # 时点枚举 pre/post/delayed；不可空
    correct: int  # 答对，0/1；不可空
    score: float | None  # 得分，仅主观题与 TAM 量表用；可空（全单选时为 None）
    qtype: str  # 题型枚举 single/blank/essay；不可空
    content_dimension: str  # 内容维度，自由字符串；可空（空串未归类）


@dataclass(frozen=True)
class CsvPayload:
    """export 契约：一份就绪的 CSV，编码固定 UTF-8 带 BOM。"""

    encoding: str  # 编码，取值 UTF8_BOM；不可空
    header: tuple[str, ...]  # 表头，中文列名；不可空
    rows: tuple[tuple, ...]  # 数据行，列数与表头一致；可为空元组


def to_csv(payload: CsvPayload) -> bytes:
    """纯函数契约：CsvPayload 转带 BOM 的字节流，缺失值用空串。"""
    ...


def check_rows(rows: tuple[SubjectRow, ...]) -> None:
    """纯函数契约：整批校验，越界枚举与负值一律拒绝，避免导出半坏数据。"""
    ...
