"""路由层的请求/响应模型。只做格式转换，不含业务规则。"""

from typing import Literal

from pydantic import BaseModel, Field

MAX_TEXT = 2_000_000


class ConfigIn(BaseModel):
    """抽取配置：OpenAI 兼容接口，开发期以 DeepSeek 为样例。"""

    provider: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=100)
    base_url: str = Field(min_length=1, max_length=500)
    timeout_s: int = Field(ge=1, le=300)
    max_chars: int = Field(ge=1, le=100000)
    enabled: bool = True
    reasoning_effort: str = Field(default="", max_length=20)

    def to_config(self):
        import kbp.contracts.extractconfig
        return kbp.contracts.extractconfig.ExtractConfig(
            provider=self.provider, model=self.model, base_url=self.base_url,
            timeout_s=self.timeout_s, max_chars=self.max_chars,
            enabled=self.enabled, reasoning_effort=self.reasoning_effort)


class ConfigOut(BaseModel):
    """配置回显：含 has_key 与 key_env，绝不含密钥本身。"""

    provider: str
    model: str
    base_url: str
    timeout_s: int
    max_chars: int
    enabled: bool
    reasoning_effort: str
    has_key: bool
    key_env: str
    error: str


class IngestIn(BaseModel):
    """按本地路径读原文。"""

    path: str = Field(min_length=1, max_length=4096)


class IngestOut(BaseModel):
    file_name: str
    source: str
    has_ocr: bool
    page_count: int
    chars: int


class UploadOut(BaseModel):
    """上传回执：教材号先行，正文回给前端接着裁 kit。"""

    material_id: int
    file_name: str
    ext: str
    source: str
    chars: int
    has_ocr: bool
    page_count: int
    text: str


class MaterialOut(BaseModel):
    material_id: int
    file_name: str
    ext: str
    chars: int
    created_at: str


class MaterialsOut(BaseModel):
    items: list[MaterialOut]


class MaterialTextOut(BaseModel):
    """旧教材的正文：按落盘文件重读一次，让学生不必重新上传。"""

    material_id: int
    file_name: str
    ext: str
    chars: int
    text: str


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
    evidence: str = ""
    suspect: bool = False


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


class SignalOut(BaseModel):
    """一条抽崩信号：原值与阈值成对带出，供界面显示与事后核对。"""

    name: str
    label: str
    value: float | None = None
    threshold: float | None = None  # 未校准时为空
    triggered: bool


class KitAutoOut(KitOut):
    """自动路：多回内容指纹，并说明这张图是复用的还是新抽的。"""

    fingerprint: str
    from_bank: bool = False  # 是否命中题库（复用旧图，未调用模型）
    possibly_inaccurate: bool = False  # 只描述本次抽取；命中题库时为 False
    message: str = ""
    signals: list[SignalOut] = []  # 同上，命中题库时为空
    calibrated: bool = False  # 抽崩阈值是否已校准；未校准时只带信号原值
    baseline_n: int = 0  # 基线样本量；单位：张；未校准时为 0
    baseline_source: str = ""  # 基线来源；未校准时为空串


class KitAutoIn(BaseModel):
    """运行期自动裁 kit：教材 + 文本 + 词表，无人裁定。"""

    material_id: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=MAX_TEXT)
    vocab: VocabIn
    map_version: str = Field(default="", max_length=50)  # 期望版本号；被占用则自动往后排
    retry: bool = False  # 抽崩后要求重抽：跳过题库复用另抽一批，旧批不动


class PreviewIn(BaseModel):
    """切段预报：只送正文，不落库。"""

    text: str = Field(min_length=1, max_length=MAX_TEXT)


class PreviewOut(BaseModel):
    """正文会被切成几段、共多少字。"""

    segments: int  # 本次抽取要送几段；单位：段
    chars: int  # 正文字数；单位：字


class JobOut(BaseModel):
    """后台裁 kit 任务：进度与结果共用一份快照。"""

    job_id: str
    state: str  # running / done / failed
    segments: int = 0  # 本次要抽的段数；切好段之后才有值
    done: int = 0  # 已抽完的段数
    error: str = ""  # state=failed 时的原因
    result: KitAutoOut | None = None  # state=done 时的裁剪结果


class ReadyOut(BaseModel):
    map_version: str
    locked: str


class Vec2In(BaseModel):
    """学生提交的一条命题，只用 kit 内零件。"""

    head_id: str = Field(min_length=1, max_length=50)
    connection: str = Field(min_length=1, max_length=100)
    tail_id: str = Field(min_length=1, max_length=50)


class SubmitIn(BaseModel):
    """提交：关联键为四元组，学习模式靠 submit_seq 区分多次提交。"""

    batch_id: str = Field(default="", max_length=100)  # 人工裁定批次；自动裁出的图走题库
    map_version: str = Field(min_length=1, max_length=50)
    mode: str
    condition: Literal["exp", "con"]  # 组别；导出要求明确到组，未分组不许提交
    is_practice: int = Field(default=0, ge=0, le=1)
    possibly_inaccurate: int = Field(default=0, ge=0, le=1)  # 来自裁 kit 时的体检
    signal_isolated: float | None = None  # 孤立概念率，0~1
    signal_coverage: float | None = None  # 连接词覆盖率，0~1
    signal_concentration: float | None = None  # 概念集中度，0~1
    signal_baseline: float | None = None  # 基线偏离度，Z 分数
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    time_point: str = Field(min_length=1, max_length=20)
    propositions: list[Vec2In] = Field(max_length=500)


class ErrorOut(BaseModel):
    kind: str
    head_id: str
    connection: str
    tail_id: str


class SubmitOut(BaseModel):
    """提交回执：分数与四类错误一次回齐，报告页不必再查。"""

    submit_seq: int
    fingerprint: str
    fms: float  # FMS，0~100；文献口径，不是 0~1
    total_propositions: int
    correct_propositions: int
    lacking: int
    excessive: int
    leaving: int
    reversed: int
    errors: list[ErrorOut]  # 学生图上的四类错误连接
    target_propositions: list[Vec2In]  # 目标图命题；报告页据此补画缺失连接，不评分


class DraftIn(BaseModel):
    """草稿：作答期可反复保存，关联键同提交。"""

    batch_id: str = Field(default="", max_length=100)
    map_version: str = Field(min_length=1, max_length=50)
    mode: str
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    time_point: str = Field(min_length=1, max_length=20)
    submit_seq: int = Field(ge=1)
    propositions: list[Vec2In] = Field(max_length=500)


class DraftOut(BaseModel):
    """草稿回执：带上该图指纹与保存时间。"""

    map_version: str
    fingerprint: str
    mode: str
    participant_id: int
    material_id: int
    time_point: str
    submit_seq: int
    propositions: list[Vec2In]
    saved_at: str


class CurrentDraftIn(BaseModel):
    """当前草稿：序号由服务端分配，前端不必知道是第几次。"""

    batch_id: str = Field(default="", max_length=100)
    map_version: str = Field(min_length=1, max_length=50)
    mode: str
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    time_point: str = Field(min_length=1, max_length=20)
    propositions: list[Vec2In] = Field(max_length=500)


class RecordOut(SubmitOut):
    """一条历史提交：换设备或刷新后仍能重开这份报告。"""

    material_id: int
    map_version: str
    mode: str
    submitted_at: str  # 提交时刻，ISO 8601
    scored: bool = True  # 取不到目标图时只回原图，不评分
    propositions: list[Vec2In] = []  # 学生当时连的命题，原样
    concepts: list[ConceptOut] = []  # 这张图的零件，含标签；报告页据此显示中文
    connections: list[str] = []  # 这张图允许的连接词


class RecordsOut(BaseModel):
    items: list[RecordOut]


class DraftsOut(BaseModel):
    items: list[DraftOut]


class ScoreOut(BaseModel):
    total_propositions: int
    correct_propositions: int
    fms: float  # FMS，0~100；文献口径，不是 0~1
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
    target_map_version: str = Field(default="", max_length=50)  # 本次作答对应的图版本
    participant_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    time_point: str
    questions: list[QuestionIn] = Field(min_length=1, max_length=500)
    answers: list[AnswerIn] = Field(max_length=500)


class QuizOut(BaseModel):
    quiz_id: str
    time_point: str
    percent: float
    answered: int
