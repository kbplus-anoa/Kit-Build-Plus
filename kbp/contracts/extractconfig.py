from collections.abc import Mapping
from dataclasses import dataclass

OPENAI_COMPATIBLE = "openai_compatible"

PROVIDERS = (OPENAI_COMPATIBLE,)

DEFAULT_PROVIDER = OPENAI_COMPATIBLE
DEFAULT_MODEL = ""
DEFAULT_BASE = ""
MAX_TIMEOUT_S = 300
DEFAULT_TIMEOUT_S = 120
KEY_ENV_NAME = "KBP_API_KEY"

KEY_ENV = {OPENAI_COMPATIBLE: KEY_ENV_NAME}

ENV_MODEL = "KBP_EXTRACT_MODEL"
ENV_BASE_URL = "KBP_EXTRACT_BASE_URL"
ENV_TIMEOUT_S = "KBP_EXTRACT_TIMEOUT_S"
ENV_MAX_CHARS = "KBP_EXTRACT_MAX_CHARS"
ENV_ENABLED = "KBP_EXTRACT_ENABLED"
ENV_REASONING = "KBP_EXTRACT_REASONING_EFFORT"

EFFORTS = ("", "low", "medium", "high")
EFFORT_LABELS = {"": "默认（不传）", "low": "低", "medium": "中", "high": "高"}

PROVIDER_LABELS = {OPENAI_COMPATIBLE: "自定义 / OpenAI 兼容"}


@dataclass(frozen=True)
class ExtractConfig:
    """extract 契约：抽取引擎的外部配置，由用户在客户端填写。

    协议统一是 OpenAI 兼容格式（/v1/chat/completions）；
    任何服务商只要兼容这套格式就能接入，不写死某一家。
    不含密钥本身：密钥从环境变量读取，不进入任何数据结构与日志。
    """

    provider: str  # 供应商，取值见 PROVIDERS；不可空
    model: str  # 模型名，由服务商决定，如 <服务商的模型 ID>；不可空
    base_url: str  # 接口根地址，不含 /v1；不可空
    timeout_s: int  # 单次请求超时；单位：秒；不可空，1~MAX_TIMEOUT_S
    max_chars: int  # 单次送入正文的最大字数；不可空，>0
    enabled: bool  # 是否启用；为 False 时不发起任何网络请求
    reasoning_effort: str = ""  # 思考强度，取值见 EFFORTS；空串表示不传，用模型默认


def config_error(config: ExtractConfig) -> str:
    """纯函数契约：配置是否可用；返回空串表示可用，否则返回中文人话原因。

    未启用时一律可用：禁用状态不需要完整配置也能通过，避免启动时被拦。
    """
    if not config.enabled:
        return ""
    if config.provider not in PROVIDERS:
        return "不支持的抽取供应商：" + str(config.provider)
    if not config.model.strip():
        return "还没填模型名，请在设置里填写服务商提供的模型名"
    if not config.base_url.startswith(("http://", "https://")):
        return "接口地址必须以 http:// 或 https:// 开头，且不带 /v1"
    if not 1 <= config.timeout_s <= MAX_TIMEOUT_S:
        return "超时须在 1~" + str(MAX_TIMEOUT_S) + " 秒之间"
    if config.max_chars <= 0:
        return "单次送入字数须为正"
    if config.reasoning_effort not in EFFORTS:
        return "思考强度只能是 low/medium/high，留空用模型默认"
    return ""


def key_env(provider: str) -> str:
    """纯函数契约：该供应商的密钥环境变量名；未知供应商返回空串。

    密钥只经由环境变量进入进程，配置结构里永远不含密钥。
    """
    return KEY_ENV.get(provider, "")


def canonical_provider(value: str) -> str:
    """纯函数契约：把历史值归一到当前枚举。

    协议只有一种，provider 现在只承担文案与密钥变量名，
    因此旧值（如 deepseek、openai）一律视为同一个兼容接口。
    """
    return value if value in PROVIDERS else OPENAI_COMPATIBLE


def default_config() -> ExtractConfig:
    """纯函数契约：空配置。地址与模型留给用户填，不预设任何服务商。"""
    return ExtractConfig(provider=DEFAULT_PROVIDER, model=DEFAULT_MODEL,
                         base_url=DEFAULT_BASE, timeout_s=DEFAULT_TIMEOUT_S,
                         max_chars=12000, enabled=True)


def from_env(values: Mapping[str, str] | None = None) -> ExtractConfig:
    """纯函数契约：把 .env 里的值读成配置；缺失或非法的项退回默认。

    键：KBP_EXTRACT_MODEL / KBP_EXTRACT_BASE_URL / KBP_EXTRACT_TIMEOUT_S /
    KBP_EXTRACT_MAX_CHARS / KBP_EXTRACT_ENABLED。密钥不在这里，只认环境变量。
    """
    import os
    src = os.environ if values is None else values
    base = default_config()

    def text(name: str, fallback: str) -> str:
        return str(src.get(name, "")).strip() or fallback

    return ExtractConfig(
        provider=DEFAULT_PROVIDER,
        model=text(ENV_MODEL, base.model),
        base_url=text(ENV_BASE_URL, base.base_url).rstrip("/"),
        timeout_s=_int(src.get(ENV_TIMEOUT_S), base.timeout_s, 1,
                       MAX_TIMEOUT_S),
        max_chars=_int(src.get(ENV_MAX_CHARS), base.max_chars, 1, 1000000),
        enabled=_truthy(src.get(ENV_ENABLED), base.enabled),
        reasoning_effort=_effort(src.get(ENV_REASONING)))


def _effort(raw) -> str:
    """思考强度：只认 EFFORTS 里的值，其余一律视为不传。"""
    text = str(raw or "").strip().lower()
    return text if text in EFFORTS else ""


def _int(raw, fallback: int, low: int, high: int) -> int:
    """取整数并夹在范围内；空值或非数字退回 fallback。"""
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    return min(max(value, low), high)


def _truthy(raw, fallback: bool) -> bool:
    """只有认识的真/假字样才改变取值；空值与看不懂的字样退回 fallback。"""
    text = str(raw or "").strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    return fallback
