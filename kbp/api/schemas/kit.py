"""裁 kit 与后台任务两块的请求/响应模型。"""

from pydantic import BaseModel, Field

from kbp.api.schemas.core import MAX_TEXT, Vec2In, VocabIn


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
    propositions: list[Vec2In] = []  # 目标图命题；开发者模式要看图并改图，故随 kit 带出


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
