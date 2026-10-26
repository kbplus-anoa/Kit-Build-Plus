import json
from pathlib import Path

import kbp.contracts.triple

MAX_CONNECTIONS = 200
REQUIRED_KEYS = ("vocab_id", "version", "connections")


class VocabError(ValueError):
    """词表文件不合法。"""


def load(path: str) -> kbp.contracts.triple.Vocab:
    """从 JSON 文件读连接词表。字段见 extract/INDEX.md。"""
    raw = json.loads(Path(path).read_text("utf-8"))
    return build(raw)


def build(raw: dict) -> kbp.contracts.triple.Vocab:
    """把已解析的 JSON 字典转成契约类型，越界即抛 VocabError。"""
    for key in REQUIRED_KEYS:
        if key not in raw:
            raise VocabError("词表缺少字段: " + key)
    return kbp.contracts.triple.Vocab(
        vocab_id=_text(raw["vocab_id"], "vocab_id"),
        vocab_version=_text(raw["version"], "version"),
        connections=_connections(raw["connections"]),
    )


def _text(value, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise VocabError(name + " 不得为空")
    return text


def _connections(value) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise VocabError("connections 必须是数组")
    items: list[str] = []
    for raw in value:
        text = str(raw or "").strip()
        if not text:
            raise VocabError("连接词不得为空")
        if text in items:
            raise VocabError("连接词重复: " + text)
        items.append(text)
    if not items:
        raise VocabError("connections 不得为空")
    if len(items) > MAX_CONNECTIONS:
        raise VocabError("连接词过多: " + str(len(items)))
    return tuple(items)
