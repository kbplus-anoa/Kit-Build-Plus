from dataclasses import dataclass

DEEPSEEK = "deepseek"

PROVIDERS = (DEEPSEEK,)

DEFAULT_MODEL = "deepseek-flash"
DEFAULT_BASE = "https://api.deepseek.com"
MAX_TIMEOUT_S = 300


@dataclass(frozen=True)
class ExtractConfig:
    """extract 契约：抽取引擎的外部配置，由用户在客户端填写。

    不含密钥本身：密钥从环境变量读取，不进入任何数据结构与日志。
    """

    provider: str  # 供应商标识，取值见 PROVIDERS；不可空
    model: str  # 模型名，如 deepseek-flash；不可空
    base_url: str  # 接口根地址，OpenAI 兼容格式；不可空
    timeout_s: int  # 单次请求超时；单位：秒；不可空，1~MAX_TIMEOUT_S
    max_chars: int  # 单次送入正文的最大字数；不可空，>0
    enabled: bool  # 是否启用；为 False 时不发起任何网络请求


def config_error(config: ExtractConfig) -> str:
    """纯函数契约：配置是否可用；返回空串表示可用，否则返回中文人话原因。

    未启用时一律可用：禁用状态不需要完整配置也能通过，避免启动时被拦。
    """
    if not config.enabled:
        return ""
    if config.provider not in PROVIDERS:
        return "不支持的抽取供应商：" + str(config.provider)
    if not config.model.strip():
        return "模型名不得为空"
    if not config.base_url.startswith(("http://", "https://")):
        return "接口地址必须以 http:// 或 https:// 开头"
    if not 1 <= config.timeout_s <= MAX_TIMEOUT_S:
        return "超时须在 1~" + str(MAX_TIMEOUT_S) + " 秒之间"
    if config.max_chars <= 0:
        return "单次送入字数须为正"
    return ""
