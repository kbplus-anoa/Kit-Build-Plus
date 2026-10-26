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


class TamScoreIn(BaseModel):
    """一次作答：某人某题得几分；得分限 1–6，越界在本层就拒掉。"""

    participant_id: int = Field(ge=1)
    item_id: str = Field(min_length=1, max_length=20)
    score: float = Field(ge=LIKERT_MIN, le=LIKERT_MAX)


class TamAlphaIn(BaseModel):
    rows: list[TamScoreIn] = Field(default_factory=list, max_length=100000)


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
