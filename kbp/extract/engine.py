import kbp.contracts.extractconfig
import kbp.contracts.triple
import kbp.extract.chat_client
import kbp.extract.normalize
import kbp.extract.prompt


class ChatEngine:
    """OpenAI 兼容接口的抽取引擎；开发期以 DeepSeek 为样例。

    协议与供应商无关：换 base_url、model 与密钥环境变量即可换服务商。
    构造不发请求、不读密钥；首次 extract 才校验密钥，便于在无密钥环境导入。
    """

    def __init__(self, transport=None) -> None:
        self._transport = transport
        self.last_raw = ""
        self.last_discards: tuple = ()

    def extract(self, text: str, vocab: kbp.contracts.triple.Vocab,
                config: kbp.contracts.extractconfig.ExtractConfig
                ) -> tuple[kbp.contracts.triple.TripleCandidate, ...]:
        """一次抽取：构造提示词、调接口、规范化。原始输出留在 last_raw。"""
        messages = kbp.extract.prompt.build(vocab, text, config)
        body = kbp.extract.chat_client.chat(config, messages,
                                            transport=self._transport)
        self.last_raw = str(body)
        cands, drops = kbp.extract.normalize.collect(body, vocab, text)
        self.last_discards = tuple(drops)
        return tuple(cands)
