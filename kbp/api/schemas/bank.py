"""题库批次的请求/响应模型：列版本、切回某一批。"""

from pydantic import BaseModel, Field


class KitVersionOut(BaseModel):
    """一批已冻结的图：版本、指纹、来源与是否已投用。"""

    map_version: str  # 版本号，如 v1；提交与导出按它筛
    fingerprint: str  # 目标图内容指纹；可空（老数据则为空串）
    vocab_version: str  # 词表版本；同教材可并存多个词表版本
    source: str  # 来源枚举，见 targetbank 契约（auto / adjudicated）
    in_use: bool  # 是否已投用；投用后该版本拒改
    created_at: str  # 入库时间，ISO 8601
    total_propositions: int  # 该图命题数；单位：条


class KitVersionsOut(BaseModel):
    """某教材的全部批次，按入库先后；旧批在前。"""

    material_id: int
    versions: list[KitVersionOut]


class KitUseIn(BaseModel):
    """切回某一批：只标为投用，不改图、不删新批。"""

    material_id: int = Field(ge=1)
    map_version: str = Field(min_length=1, max_length=50)


class KitUseOut(BaseModel):
    """切回回执：版本与投用标记。"""

    material_id: int
    map_version: str
    in_use: bool
