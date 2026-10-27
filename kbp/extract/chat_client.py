import json
import os

import httpx

import kbp.contracts.extractconfig

CHAT_PATH = "/v1/chat/completions"
MAX_RETRY = 2
RETRY_STATUS = (429, 500, 502, 503, 504)
BRIEF_CHARS = 200


class ApiError(RuntimeError):
    """调用失败。message 里不含密钥与请求原文。"""


class MissingKey(ApiError):
    """未配置密钥。"""


class EmptyContent(ApiError):
    """官方文档说明：JSON Output 有概率返回空 content。"""


def api_key(config: kbp.contracts.extractconfig.ExtractConfig) -> str:
    """按供应商取密钥；只读环境变量，绝不落到任何数据结构里。"""
    env = kbp.contracts.extractconfig.key_env(config.provider)
    if not env:
        raise MissingKey("不支持的抽取供应商：" + str(config.provider))
    key = os.environ.get(env, "").strip()
    if not key:
        raise MissingKey("未配置 " + env + "，抽取不可用")
    return key


def has_key(config: kbp.contracts.extractconfig.ExtractConfig) -> bool:
    env = kbp.contracts.extractconfig.key_env(config.provider)
    return bool(env and os.environ.get(env, "").strip())


def endpoint(config: kbp.contracts.extractconfig.ExtractConfig) -> str:
    """OpenAI 兼容根地址 + /v1/chat/completions。"""
    return config.base_url.rstrip("/") + CHAT_PATH


def chat(config: kbp.contracts.extractconfig.ExtractConfig,
         messages: list[dict], transport=None) -> dict:
    """发一次请求并返回解析后的 JSON 对象；空内容与限流按次数重试。"""
    payload = {
        "model": config.model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "stream": False,
    }
    if config.reasoning_effort:
        payload["reasoning_effort"] = config.reasoning_effort
    last = ""
    for attempt in range(MAX_RETRY + 1):
        try:
            return _parse(_post(config, payload, transport))
        except EmptyContent as exc:
            last = str(exc)
        except ApiError as exc:
            last = str(exc)
            if not _retryable(exc) or attempt >= MAX_RETRY:
                raise ApiError(last) from None
    raise ApiError(last or "调用失败")


def _retryable(exc: ApiError) -> bool:
    text = str(exc)
    for status in RETRY_STATUS:
        if "status=" + str(status) in text:
            return True
    return False


def _post(config, payload, transport) -> dict:
    headers = {"Authorization": "Bearer " + api_key(config),
               "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=config.timeout_s, transport=transport) as client:
            resp = client.post(endpoint(config), json=payload, headers=headers)
    except httpx.TimeoutException as exc:
        raise ApiError("网络错误：" + type(exc).__name__ + "，等了 "
                       + str(config.timeout_s) + " 秒没有回应；"
                       "可在设置里调大超时，或调小单次送入字数") from None
    except httpx.HTTPError as exc:
        raise ApiError("网络错误：" + type(exc).__name__) from None
    if resp.status_code != 200:
        raise ApiError("接口返回异常 status=" + str(resp.status_code)
                       + " " + _brief(resp.text))
    return resp.json()


def _brief(text: str) -> str:
    """截取错误信息，防止把整段请求回显进日志。"""
    return (text or "")[:BRIEF_CHARS].replace("\n", " ")


def message_content(body: dict) -> str:
    """取出 assistant 的文本内容；结构缺失时抛 ApiError。"""
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ApiError("响应缺少 choices") from None
    if not content or not content.strip():
        raise EmptyContent("模型返回空内容（官方已知问题），重试中")
    return content


def _parse(body: dict) -> dict:
    try:
        parsed = json.loads(message_content(body))
    except json.JSONDecodeError:
        raise ApiError("模型返回的不是合法 json") from None
    if not isinstance(parsed, dict):
        raise ApiError("模型返回的 json 不是对象")
    return parsed
