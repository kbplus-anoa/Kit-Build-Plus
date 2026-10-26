"""TAM 量表条目：14 题，四个构念。

题干逐字取自用户提供的问卷 `https://www.wjx.cn/vm/wEMzgZc.aspx`，
**不收人口学两题**（性别、年龄段）；态度 ATT 在源问卷标为可选，故标 `optional`。
源问卷自称五点 Likert，本项目按 SPEC 用六点（1 强不同意 … 6 强同意），
只取题目、不取锚点。
"""

from kbp.contracts.tam import ATT, BI, PEOU, PU, ScaleItem

TAM_ITEMS = (
    ScaleItem("PU1", PU, "使用该系统让我更高效地完成回忆任务。"),
    ScaleItem("PU2", PU, "系统提供的信息能够有效减少回忆中的检索难度。"),
    ScaleItem("PU3", PU, "在回忆过程中，系统提供的信息是有帮助的。"),
    ScaleItem("PU4", PU, "总体而言，我认为系统提高了我的回忆速度与正确性。"),
    ScaleItem("PEOU1", PEOU, "使用系统时，我觉得操作很简单。"),
    ScaleItem("PEOU2", PEOU, "系统提供的信息是清晰、易于理解的。"),
    ScaleItem("PEOU3", PEOU, "我能够轻松适应系统提供的动态调整（如信息量、语速）。"),
    ScaleItem("PEOU4", PEOU, "总体而言，我觉得系统易于使用。"),
    ScaleItem("BI1", BI, "如果有机会，我愿意在日常生活中使用回忆辅助系统。"),
    ScaleItem("BI2", BI, "我会向其他人推荐使用回忆辅助系统。"),
    ScaleItem("BI3", BI, "总体而言，我认为回忆辅助系统是值得长期使用的。"),
    ScaleItem("ATT1", ATT, "我觉得使用回忆辅助系统是一个好主意。", optional=True),
    ScaleItem("ATT2", ATT, "我使用系统的体验是愉快的。", optional=True),
    ScaleItem("ATT3", ATT, "总体而言，我对系统的态度是积极的。", optional=True),
)


def items_of(construct: str) -> tuple[ScaleItem, ...]:
    """取某构念的全部条目；构念代码不认识时返回空元组。"""
    return tuple(i for i in TAM_ITEMS if i.construct == construct)


def item_ids() -> frozenset[str]:
    """全部题号；用于校验作答里出现的题号。"""
    return frozenset(i.item_id for i in TAM_ITEMS)
