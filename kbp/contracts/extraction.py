from dataclasses import dataclass
from typing import Protocol

from kbp.contracts.extractconfig import ExtractConfig
from kbp.contracts.triple import TripleCandidate, Vocab


@dataclass(frozen=True)
class ExtractionRecord:
    """extract 契约：一次抽取的留档，供事后追溯“这条命题当初怎么抽出来的”。

    不存原文本身：只存原文指纹与统计量，教材正文由 ingest 自己缓存，
    避免同一份教材在库里存两遍。
    """

    batch_id: str  # 抽取批次标识，与 kit 的裁定批次对应；不可空
    vocab: Vocab  # 本次使用的词表；不可空
    config: ExtractConfig  # 本次使用的配置快照（不含密钥）；不可空
    text_sha256: str  # 原文指纹，十六进制；不可空
    chars: int  # 送入模型的原文总字数；单位：字；不可空，>=0
    sections: int  # 送入模型的正文段数；单位：段；不可空，>=0
    raw: str  # 模型的原始输出（逐段拼接的 json 文本）；可空（全部为空内容时为空串）
    triples: tuple[TripleCandidate, ...]  # 规范化后的候选三元组；可为空元组
    created_at: str  # 抽取时间，ISO 8601；不可空
    map_version: str = ""  # 冻结成图后的版本号；可空（尚未冻结时为空串）
    fingerprint: str = ""  # 冻结成图后的内容指纹；可空（尚未冻结时为空串）


class ExtractPort(Protocol):
    """行为契约：抽取引擎。

    实现方可直调云端，也可在测试里用假引擎；
    返回的每条三元组必须已落在词表内，越界由实现方丢弃，调用方不再过滤。
    """

    def extract(self, text: str, vocab: Vocab,
                config: ExtractConfig) -> tuple[TripleCandidate, ...]: ...


class ExtractionStore(Protocol):
    """行为契约：抽取留档的存储。

    留档用于追溯与回调基线，不进 CSV；原文正文不在这里存，
    同一份教材只由 ingest 缓存一次（D10 的缓存与这里不是同一对象）。
    """

    def save(self, record: ExtractionRecord) -> None:
        """写一条留档；同一批次重复写须拒绝。"""
        ...

    def load(self, batch_id: str) -> ExtractionRecord | None:
        """按批次读回；没有返回 None。"""
        ...

    def by_text(self, text_sha256: str) -> tuple[ExtractionRecord, ...]:
        """同一份原文的全部抽取批次，按入库先后排列；没有返回空元组。"""
        ...

    def attach_map(self, batch_id: str, map_version: str,
                   fingerprint: str) -> None:
        """留档与冻结后的图对账：回填版本号与指纹；批次不存在须拒绝。"""
        ...
