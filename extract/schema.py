import json
import triple


def to_schema(vocab: triple.Vocab) -> dict:
    """把连接词表转成 UIE 的 schema：键是"概念"，值就是连接词本身。"""
    return {"概念": list(vocab.connections)}


def to_schema_json(vocab: triple.Vocab) -> str:
    return json.dumps(to_schema(vocab), ensure_ascii=False)


def validate_vocab(vocab: triple.Vocab) -> None:
    """断言词表可用于抽取：非空、无重复、无空串。"""
    if not vocab.connections:
        raise ValueError("连接词表为空，无法抽取")
    seen = set()
    for item in vocab.connections:
        if not item.strip():
            raise ValueError("连接词含空串")
        if item in seen:
            raise ValueError("连接词重复: " + item)
        seen.add(item)
