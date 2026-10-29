"""开发者模式的请求/响应模型：整份改写与撤销。"""

from pydantic import BaseModel, Field

from kbp.api.schemas.core import Vec2In
from kbp.api.schemas.kit import ConceptOut, KitOut


class DevKitIn(BaseModel):
    """整份改写：概念、连接词与目标命题一起给，缺一块即不完整的图。"""

    material_id: int = Field(ge=1)
    map_version: str = Field(min_length=1, max_length=50)
    password: str = Field(max_length=100)
    concepts: list[ConceptOut]
    connections: list[str]
    propositions: list[Vec2In]


class DevKitOut(KitOut):
    """改写回包：同 kit，另说这一批有没有被改过、改于何时。"""

    edited: bool = False
    updated_at: str = ""
