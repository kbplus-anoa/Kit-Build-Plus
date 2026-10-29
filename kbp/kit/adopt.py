"""人工裁定路的入库：把开发期冻结的图登记进题库，与自动路共用一张表。

裁定记录本身不带教材标识，教材只能由调用方给：提交与草稿的请求里已有
material_id，裁 kit 预览没有，所以预览不登记，首次用到时才入库。
"""

from datetime import datetime, timezone

import kbp.contracts.targetbank
import kbp.contracts.targetmap


def now() -> str:
    """入库时间，ISO 8601。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def entry(material_id: int, batch_id: str,
          target: kbp.contracts.targetmap.TargetMap,
          created_at: str) -> kbp.contracts.targetbank.BankEntry:
    """包成登记项：来源标 adjudicated，带上来源批次便于回溯裁定记录。"""
    return kbp.contracts.targetbank.BankEntry(
        material_id=material_id, vocab_version=target.vocab.vocab_version,
        source=kbp.contracts.targetbank.ADJUDICATED, in_use=False,
        created_at=created_at, target_map=target, batch_id=batch_id)
