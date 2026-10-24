from dataclasses import dataclass

UTF8_BOM = "utf-8-sig"


@dataclass(frozen=True)
class SubjectRow:
    """export 契约：被试级一行，只读 score 结果不重算分。"""

    participant_id: int  # 被试顺序编号；不可空
    material_id: int  # 教材顺序编号；不可空
    target_map_version: str  # 目标图版本，如 v1；不可空
    session: int  # 场次，自然数递增含练习；不可空，>=1
    mode: str  # 模式枚举 test/study；不可空
    condition: str  # 组别枚举 exp/con；不可空
    correct_propositions: int  # 评分分子；单位：条；不可空
    total_propositions: int  # 评分分母；单位：条；不可空


@dataclass(frozen=True)
class CsvPayload:
    """export 契约：一份就绪的 CSV，编码固定 UTF-8 带 BOM。"""

    encoding: str  # 编码，取值 UTF8_BOM；不可空
    header: tuple[str, ...]  # 表头，中文列名；不可空
    rows: tuple[tuple[str, ...], ...]  # 数据行，均为字符串；可为空元组


def to_csv(payload: CsvPayload) -> bytes:
    """纯函数契约：CsvPayload 转带 BOM 的字节流，缺失值用空串。"""
    ...
