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
    participant_id: int  # 被试顺序编号，关联键之一；不可空，>=1
    material_id: int  # 教材顺序编号，关联键之一；不可空，>=1
    session: int  # 场次，含练习，关联键之一；不可空，>=1


@dataclass(frozen=True)
class Draft:
    """rebuild 契约：中途保存的草稿，允许被覆盖直到提交。"""

    map_version: str  # 学生所用目标图版本；不可空
    mode: str  # 模式枚举；不可空，选定后不可换
    propositions: tuple[SubmittedProposition, ...]  # 当前已连的命题；可为空元组
    participant_id: int  # 被试顺序编号；不可空，>=1
    material_id: int  # 教材顺序编号；不可空，>=1
    session: int  # 场次；不可空，>=1
    saved_at: str  # 保存时间，ISO 8601；不可空
