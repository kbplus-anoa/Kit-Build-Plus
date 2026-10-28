"""建图提交与历史记录两块的请求/响应模型。"""

from typing import Literal

from pydantic import BaseModel, Field

from kbp.api.schemas.kit import ConceptOut


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
