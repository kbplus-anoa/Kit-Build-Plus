from dataclasses import dataclass

PRE = "pre"
POST = "post"
DELAYED = "delayed"

TIME_POINTS = (PRE, POST, DELAYED)

SINGLE = "single"
BLANK = "blank"
ESSAY = "essay"

QUESTION_TYPES = (SINGLE, BLANK, ESSAY)

MAX_CHOICES = 8
MAX_STEM = 2000


@dataclass(frozen=True)
class Question:
    """quiz 契约：一道题，客观单选为 MVP 唯一形态。"""

    question_id: str  # 题号，同一测验内唯一；不可空
    stem: str  # 题干，长度 <= MAX_STEM；不可空
    choices: tuple[str, ...]  # 选项，单选须 >=2 且 <= MAX_CHOICES；不可空
    answer_index: int  # 正确选项下标，0 基；不可空，须落在 choices 范围内
    qtype: str  # 题型枚举，取值见 QUESTION_TYPES；不可空
    content_dimension: str  # 内容维度，自由字符串先不收枚举；可空（空串未归类）


@dataclass(frozen=True)
class Answer:
    """quiz 契约：学生对一道题的作答。"""

    question_id: str  # 题号，须存在于所属测验；不可空
    choice_index: int  # 所选下标，0 基；不可空，缺答用 -1 表示未作答
    time_point: str  # 时点枚举，取值见 TIME_POINTS；不可空


@dataclass(frozen=True)
class QuizRecord:
    """quiz 契约：一人在一个时点的整卷作答，long 表的一行来源。"""

    quiz_id: str  # 整卷标识，同卷可多次施测；不可空
    participant_id: int  # 被试顺序编号，关联键之一；不可空，>=1
    material_id: int  # 教材顺序编号，关联键之一；不可空，>=1
    session: int  # 场次，关联键之一；不可空，>=1
    time_point: str  # 时点枚举；不可空
    answers: tuple[Answer, ...]  # 作答项，可为空元组


def is_correct(question: Question, answer: Answer) -> bool:
    """纯函数契约：是否答对；未作答（-1）一律算错。"""
    ...


def percent_score(questions: tuple[Question, ...],
                  record: QuizRecord) -> float:
    """纯函数契约：百分制分数 0–100，分母为题数，题数为 0 时取 0.0。"""
    ...
