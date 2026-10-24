from dataclasses import dataclass

TEST = "test"
STUDY = "study"

MODES = (TEST, STUDY)


@dataclass(frozen=True)
class SubmittedProposition:
    """rebuild 契约：学生提交的一条命题，只能由 kit 零件组成。"""

    head_id: str  # 起端概念 id，须来自 Kit.concepts；不可空
    connection: str  # 连接词，须来自 Kit.connections；不可空
    tail_id: str  # 末端概念 id，须来自 Kit.concepts；不可空


@dataclass(frozen=True)
class Submission:
    """rebuild 契约：一次提交的完整快照，重建层不做对错判断。"""

    map_version: str  # 学生所用目标图版本；不可空
    mode: str  # 模式枚举，取值见 MODES；不可空，进画布前已锁定
    propositions: tuple[SubmittedProposition, ...]  # 学生建出的命题；可为空元组
    started_at: str  # 建图开始时间，ISO 8601；可空（未记录则空串）
    submitted_at: str  # 提交时间，ISO 8601；不可空
