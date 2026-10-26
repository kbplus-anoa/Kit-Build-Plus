import kbp.contracts.extractconfig
import kbp.contracts.triple

SYSTEM = """你正在为概念图教学系统抽取命题。规则：

1. 只使用给定的连接词，一个都不许新造。
2. 每条命题是「主语 -连接词-> 宾语」的有向三元组，方向必须与原文一致。
   原文说「A 属于 B」，就写 A 属于 B，绝不能反过来。
3. 一个句子里有多个命题时，逐条写出。并列结构要展开：
   「A 包括 B、C、D」→ 三条：A 包括 B；A 包括 C；A 包括 D。
   但绝不能写出 B 包括 C 这类原文没有的关系。
4. 概念用原文中的原词，不要改写、不要翻译、不要概括。
5. evidence 填该命题所依据的原文片段，逐字摘取，不超过 60 字。
6. 如果这段原文里没有任何符合上述规则的命题，返回空数组。

只输出 json，格式严格如下：
{
  "propositions": [
    {"head": "主语原词", "connection": "连接词", "tail": "宾语原词",
     "evidence": "原文片段"}
  ]
}
"""


def build(vocab: kbp.contracts.triple.Vocab, text: str,
          config: kbp.contracts.extractconfig.ExtractConfig
          | None = None) -> list[dict]:
    """构造 chat 消息。正文超长时截断，避免一次请求过大。"""
    limit = config.max_chars if config is not None else 12000
    body = text.strip()[:limit] if text else ""
    user = ("可用连接词（只能从中选）：" + "、".join(vocab.connections)
            + "\n\n原文：\n" + body)
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
