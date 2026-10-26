"""DeepSeek（OpenAI 兼容格式）的最小 HTTP 客户端。

只用 httpx 与标准库，不引入 openai SDK。
密钥只从环境变量读取，不进任何数据结构、不进日志、不进异常信息。
"""

import json
import os

import httpx

import kbp.contracts.extractconfig

ENV_KEY = "DEEPSEEK_API_KEY"
CHAT_PATH = "/chat/completions"
MAX_RETRY = 2
RETRY_STATUS = (429, 500, 502, 503, 504)


class ApiError(RuntimeError):
    """调用失败。message 里不含密钥与请求原文。"""


class MissingKey(ApiError):
    """未配置密钥。"""


class EmptyContent(ApiError):
    """官方文档说明：JSON Output 有概率返回空 content。"""


def api_key() -> str:
    key = os.environ.get(ENV_KEY, "").strip()
    if not key:
        raise MissingKey("未配置 " + ENV_KEY + "，抽取不可用")
    return key


def has_key() -> bool:
    return bool(os.environ.get(ENV_KEY, "").strip())


def endpoint(config: kbp.contracts.extractconfig.ExtractConfig) -> str:
    return config.base_url.rstrip("/") + "/v1" + CHAT_PATH


def chat(config: kbp.contracts.extractconfig.ExtractConfig, messages: list[dict],
         transport=None) -> dict:
    """发一次请求并返回解析后的 JSON 对象；内容为空时抛 EmptyContent。"""
    payload = {
        "model": config.model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "stream": False,
    }
    last = ""
    for attempt in range(MAX_RETRY + 1):
        try:
            return _parse(_post(config, payload, transport))
        except EmptyContent as exc:
            last = str(exc)
        except ApiError as exc:
            if "status=" not in str(exc):
                raise
            last = str(exc)
            if attempt >= MAX_RETRY:
                raise ApiError(last) from None
    raise ApiError(last or "调用失败")


def _post(config, payload, transport) -> dict:
    headers = {"Authorization": "Bearer " + api_key(),
               "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=config.timeout_s, transport=transport) as client:
            resp = client.post(endpoint(config), json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise ApiError("网络错误：" + type(exc).__name__) from None
    if resp.status_code != 200:
        raise ApiError("接口返回异常 status=" + str(resp.status_code)
                       + " " + _brief(resp.text))
    return resp.json()


def _brief(text: str) -> str:
    """截取错误信息，防止把整段请求回显进日志。"""
    return (text or "")[:200].replace("\n", " ")


def _parse(body: dict) -> dict:
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ApiError("响应缺少 choices") from None
    if not content or not content.strip():
        raise EmptyContent("模型返回空内容（官方已知问题），重试中")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise ApiError("模型返回的不是合法 json") from None
    if not isinstance(parsed, dict):
        raise ApiError("模型返回的 json 不是对象")
    return parsed
