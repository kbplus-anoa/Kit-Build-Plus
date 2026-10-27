"""TAM 路由的请求/响应模型。只做格式转换，不含业务规则。"""

from pydantic import BaseModel, Field

from kbp.contracts.tam import LIKERT_MAX, LIKERT_MIN


class TamItemOut(BaseModel):
    item_id: str
    construct_code: str  # 构念代码，如 PU；契约字段名 construct 与 BaseModel 自带的弃用方法撞名
    construct_label: str
    text: str
    optional: bool = False


class TamConstructOut(BaseModel):
    code: str
    label: str


class TamItemsOut(BaseModel):
    """量表全貌：六点上下限、判据、构念中文名与全部条目。"""

    likert_min: int
    likert_max: int
    min_alpha: float
    constructs: list[TamConstructOut]
    items: list[TamItemOut]


class TamAnswerIn(BaseModel):
    """一题的作答：题号须在量表内，得分限 1–6，越界在本层就拒掉。"""

    item_id: str = Field(min_length=1, max_length=20)
    score: float = Field(ge=LIKERT_MIN, le=LIKERT_MAX)


class TamAnswersIn(BaseModel):
    """整份量表作答：落库后 α 只从库算，不再由调用方送数。"""

    participant_id: int = Field(ge=1)
    answered_at: str = Field(default="", max_length=40)  # ISO 8601；空串取服务端当前时间
    answers: list[TamAnswerIn] = Field(min_length=1, max_length=100)


class TamSavedOut(BaseModel):
    participant_id: int
    saved: int


class TamAlphaReportOut(BaseModel):
    construct_code: str
    construct_label: str
    k: int
    n: int
    alpha: float | None = None
    threshold: float
    passed: bool


class TamAlphaOut(BaseModel):
    reports: list[TamAlphaReportOut]
