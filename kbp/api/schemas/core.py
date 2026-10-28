"""配置、读稿与抽取三块的请求/响应模型。"""

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
