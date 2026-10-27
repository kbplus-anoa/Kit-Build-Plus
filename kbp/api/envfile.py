"""读仓库根的 .env，把其中的键补进进程环境；已存在的环境变量优先。

格式只需要 KEY=VALUE：注释、空行、没有等号的行跳过；
值两端的引号会去掉。不引入 dotenv 依赖。
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NAME = ".env"
_FROM_FILE: set = set()


def path() -> Path:
    """env 文件位置；可用 KBP_ENV_FILE 指到别处，默认仓库根 .env。"""
    raw = os.environ.get("KBP_ENV_FILE", "").strip()
    return Path(raw) if raw else ROOT / DEFAULT_NAME


def parse(text: str) -> dict:
    """解析 KEY=VALUE 文本；只认第一次出现的等号。"""
    pairs = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key:
            pairs[key] = _unquote(value.strip())
    return pairs


def apply(target=None) -> dict:
    """把 .env 补进环境变量，返回真正补进去的键；文件不在就什么都不做。"""
    env = os.environ if target is None else target
    applied = {}
    for key, value in _read().items():
        if key in env:
            continue
        env[key] = value
        applied[key] = value
    if target is None:
        _FROM_FILE.update(applied)
    return applied


def reload() -> dict:
    """重读 .env 但不重启进程：只改上次由文件写入的键，shell 里设的键仍优先。"""
    updated = {}
    for key, value in _read().items():
        current = os.environ.get(key, "")
        if key not in _FROM_FILE and current:
            continue
        _FROM_FILE.add(key)
        if current == value:
            continue
        os.environ[key] = value
        updated[key] = value
    return updated


def _read() -> dict:
    try:
        return parse(path().read_text(encoding="utf-8-sig"))
    except OSError:
        return {}


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value
