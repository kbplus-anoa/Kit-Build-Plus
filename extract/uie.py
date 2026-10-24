import triple


class UieUnavailable(RuntimeError):
    """PaddleNLP 或 UIE 权重不可用。"""


class UieExtractor:
    """UIE 模型适配器：实现 contract-share 的 ExtractorPort 语义。

    权重在第一次调用时才加载，构造本对象不触发任何 IO。
    """

    def __init__(self, model: str = "uie-base", device: str = "cpu",
                 batch_size: int = 8) -> None:
        self._model_name = model
        self._device = device
        self._batch_size = batch_size
        self._engine = None

    def _load(self):
        if self._engine is not None:
            return self._engine
        try:
            from paddlenlp import Taskflow
        except Exception as exc:
            raise UieUnavailable("未安装 paddlenlp，UIE 抽取不可用") from exc
        self._engine = Taskflow(
            "information_extraction",
            schema=[],
            model=self._model_name,
            device=self._device,
            batch_size=self._batch_size,
        )
        return self._engine

    def extract(self, text: str, schema: dict) -> list[dict]:
        """对单段文本执行一次 UIE 抽取，返回原始结果条列表。"""
        engine = self._load()
        engine.set_schema(schema)
        result = engine(text)
        return list(result or [])


def raw_to_triples(raw: list[dict], vocab: triple.Vocab) -> list[triple.TripleCandidate]:
    """把 UIE 的原始输出转成候选三元组，越出词表的连接词直接丢弃。"""
    allowed = set(vocab.connections)
    out: list[triple.TripleCandidate] = []
    for entry in raw:
        for connection, items in (entry or {}).items():
            if connection not in allowed:
                continue
            out.extend(_pairs(connection, items))
    return out


def _pairs(connection: str, items) -> list[triple.TripleCandidate]:
    nodes = [it for it in (items or []) if it.get("text")]
    out = []
    for head in nodes:
        for tail in nodes:
            if head is tail:
                continue
            out.append(triple.TripleCandidate(
                head=head["text"], connection=connection,
                tail=tail["text"], confidence=_conf(head, tail)))
    return out


def _conf(head: dict, tail: dict) -> float:
    return float(min(head.get("probability", 0.5),
                     tail.get("probability", 0.5)))
