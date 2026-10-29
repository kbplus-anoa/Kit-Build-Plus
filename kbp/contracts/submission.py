from dataclasses import dataclass

TEST = "test"
STUDY = "study"

MODES = (TEST, STUDY)

PRE = "pre"
POST = "post"
DELAYED = "delayed"

TIME_POINTS = (PRE, POST, DELAYED)

KEY_FIELDS = ("participant_id", "material_id", "time_point", "submit_seq")


def check_key(participant_id: int, material_id: int, time_point: str,
              submit_seq: int) -> str:
    """纯函数契约：四元关联键是否合法；返回空串表示合法，否则返回中文原因。

    关联键 = 被试标识 + 教材 + 时点 + 提交序号，四个键都非空。
    """
    for name, value in (("participant_id", participant_id),
                        ("material_id", material_id),
                        ("submit_seq", submit_seq)):
        if not isinstance(value, int) or value < 1:
            return name + " 须为正整数"
    if time_point not in TIME_POINTS:
        return "未知时点: " + str(time_point)
    return ""


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
    fingerprint: str  # 学生所用目标图的内容指纹；不可空（筛同批人靠它）
    mode: str  # 模式枚举，取值见 MODES；不可空，进画布前已锁定
    propositions: tuple[SubmittedProposition, ...]  # 学生建出的命题；可为空元组
    started_at: str  # 建图开始时间，ISO 8601；可空（未记录则空串）
    submitted_at: str  # 提交时间，ISO 8601；不可空
    participant_id: int  # 被试顺序编号，关联键之一；不可空，>=1
    material_id: int  # 教材顺序编号，关联键之一；不可空，>=1
    time_point: str  # 时点枚举，取值见 TIME_POINTS；不可空
    submit_seq: int  # 提交序号，同一被试同一教材同一时点的第几次提交，从 1 起；不可空，>=1


@dataclass(frozen=True)
class Draft:
    """rebuild 契约：中途保存的草稿，允许被覆盖直到测验模式提交。"""

    map_version: str  # 学生所用目标图版本；不可空
    fingerprint: str  # 学生所用目标图的内容指纹；不可空
    mode: str  # 模式枚举；不可空，选定后不可换
    propositions: tuple[SubmittedProposition, ...]  # 当前已连的命题；可为空元组
    participant_id: int  # 被试顺序编号，关联键之一；不可空，>=1
    material_id: int  # 教材顺序编号，关联键之一；不可空，>=1
    time_point: str  # 时点枚举，取值见 TIME_POINTS；不可空
    submit_seq: int  # 这份草稿对应的提交序号，从 1 起；不可空，>=1
    saved_at: str  # 保存时间，ISO 8601；不可空
