"""路由层的请求/响应模型。只做格式转换，不含业务规则。"""

from pydantic import BaseModel, Field

MAX_TEXT = 2_000_000


class IngestIn(BaseModel):
    """按本地路径读原文。"""

    path: str = Field(min_length=1, max_length=4096)


class IngestOut(BaseModel):
    file_name: str
    source: str
    has_ocr: bool
    page_count: int
    chars: int


class VocabIn(BaseModel):
    """连接词表，顺序即 schema 顺序。"""

    vocab_id: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    connections: list[str] = Field(min_length=1, max_length=200)


class ExtractIn(BaseModel):
    """抽取请求：文本 + 词表。"""

    text: str = Field(min_length=0, max_length=MAX_TEXT)
    vocab: VocabIn


class TripleOut(BaseModel):
    head: str
    connection: str
    tail: str
    confidence: float


class ExtractOut(BaseModel):
    vocab_id: str
    vocab_version: str
    count: int
    triples: list[TripleOut]


class AdjudicationIn(BaseModel):
    """一条裁定：候选三元组 + 决定。"""

    head: str = Field(min_length=1, max_length=500)
    connection: str = Field(min_length=1, max_length=100)
    tail: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    decision: str
    reason: str = Field(default="", max_length=500)


class BatchIn(BaseModel):
    """整批裁定，驳回项一并留档。"""

    batch_id: str = Field(min_length=1, max_length=100)
    vocab: VocabIn
    items: list[AdjudicationIn] = Field(max_length=5000)


class BatchOut(BaseModel):
    batch_id: str
    saved: int


class BuildKitIn(BaseModel):
    batch_id: str = Field(min_length=1, max_length=100)
    map_version: str = Field(min_length=1, max_length=50)


class ConceptOut(BaseModel):
    concept_id: str
    label: str


class KitOut(BaseModel):
    map_version: str
    concepts: list[ConceptOut]
    connections: list[str]
    total_propositions: int


class ReadyOut(BaseModel):
    map_version: str
    locked: str


class Vec2In(BaseModel):
    """学生提交的一条命题，只用 kit 内零件。"""

    head_id: str = Field(min_length=1, max_length=50)
    connection: str = Field(min_length=1, max_length=100)
    tail_id: str = Field(min_length=1, max_length=50)


class SubmitIn(BaseModel):
    batch_id: str = Field(min_length=1, max_length=100)
    map_version: str = Field(min_length=1, max_length=50)
    mode: str
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    session: int = Field(ge=1)
    propositions: list[Vec2In] = Field(max_length=500)


class ErrorOut(BaseModel):
    kind: str
    head_id: str
    connection: str
    tail_id: str


class ScoreOut(BaseModel):
    total_propositions: int
    correct_propositions: int
    score: float
    lacking: int
    excessive: int
    leaving: int
    reversed: int
    errors: list[ErrorOut]


class AnswerIn(BaseModel):
    question_id: str = Field(min_length=1, max_length=50)
    choice_index: int = Field(ge=-1, le=7)


class QuestionIn(BaseModel):
    question_id: str = Field(min_length=1, max_length=50)
    stem: str = Field(min_length=1, max_length=2000)
    choices: list[str] = Field(min_length=2, max_length=8)
    answer_index: int = Field(ge=0, le=7)
    qtype: str
    content_dimension: str = Field(default="", max_length=200)


class QuizIn(BaseModel):
    quiz_id: str = Field(min_length=1, max_length=100)
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    session: int = Field(ge=1)
    time_point: str
    questions: list[QuestionIn] = Field(min_length=1, max_length=500)
    answers: list[AnswerIn] = Field(max_length=500)


class QuizOut(BaseModel):
    quiz_id: str
    time_point: str
    percent: float
    answered: int


class SubjectRowIn(BaseModel):
    """被试级一行，字段与 CSV_PLAN A–F 节对应。"""

    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    target_map_version: str = Field(min_length=1, max_length=50)
    session: int = Field(ge=1)
    mode: str
    condition: str
    is_practice: int = Field(ge=0, le=1)
    correct_propositions: int = Field(ge=0)
    total_propositions: int = Field(ge=0)
    n_lacking: int = Field(ge=0)
    n_excessive: int = Field(ge=0)
    n_leaving: int = Field(ge=0)
    n_reversed: int = Field(ge=0)
    possibly_inaccurate: int = Field(ge=0, le=1)
    map_size: int = Field(ge=0)
    map_node_count: int = Field(ge=0)
    signal_isolated: float | None = None
    signal_coverage: float | None = None
    signal_concentration: float | None = None
    signal_baseline: float | None = None


class SubjectExportIn(BaseModel):
    rows: list[SubjectRowIn] = Field(min_length=1, max_length=10000)


class QuestionRowIn(BaseModel):
    """题级一行，字段与 CSV_PLAN H 节对应。"""

    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    target_map_version: str = Field(min_length=1, max_length=50)
    session: int = Field(ge=1)
    question_id: str = Field(min_length=1, max_length=50)
    time_point: str
    correct: int = Field(ge=0, le=1)
    score: float | None = None
    qtype: str
    content_dimension: str = Field(default="", max_length=200)


class QuestionExportIn(BaseModel):
    rows: list[QuestionRowIn] = Field(min_length=1, max_length=100000)
