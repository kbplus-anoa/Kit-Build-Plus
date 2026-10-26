from dataclasses import dataclass

LACKING = "lacking"
EXCESSIVE = "excessive"
LEAVING = "leaving"
REVERSED = "reversed"

ERROR_KINDS = (LACKING, EXCESSIVE, LEAVING, REVERSED)

FMS_MIN = 0.0
FMS_MAX = 100.0


@dataclass(frozen=True)
class ErrorChain:
    """score 契约：一条错误连接，只进报告不影响分数。"""

    kind: str  # 错误类别枚举，取值见 ERROR_KINDS；不可空
    head_id: str  # 起端概念 id；不可空
    connection: str  # 连接词；不可空
    tail_id: str  # 末端概念 id；不可空


@dataclass(frozen=True)
class ScoreResult:
    """score 契约：命题级精确匹配结果，分数只存原始分子分母。"""

    total_propositions: int  # 目标命题总数，即评分分母；单位：条；不可空，>=0
    correct_propositions: int  # 正确命题数，即评分分子；单位：条；不可空，0~分母
    errors: tuple[ErrorChain, ...]  # 四类错误连接；可为空元组


def fms(result: ScoreResult) -> float:
    """纯函数契约：FMS = 正确命题数 / 目标命题总数 × 100。

    量纲 0~100（文献口径），分母为 0 时取 0.0；保留 4 位小数。
    派生量不存库，取用时才算，避免锁死公式。
    """
    ...
