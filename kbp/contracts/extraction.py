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


class ExtractPort(Protocol):
    """行为契约：抽取引擎。

    实现方可直调云端，也可在测试里用假引擎；
    返回的每条三元组必须已落在词表内，越界由实现方丢弃，调用方不再过滤。
    """

    def extract(self, text: str, vocab: Vocab,
                config: ExtractConfig) -> tuple[TripleCandidate, ...]: ...
